import json, hmac, hashlib
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import get_db
from .dependencies import company_user
from .models import User
from .models_enterprise import Subscription
from .config import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, RAZORPAY_WEBHOOK_SECRET, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET
router=APIRouter(prefix='/api/billing',tags=['Subscriptions & Billing'])
class CheckoutIn(BaseModel): provider:str=Field(pattern='^(razorpay|stripe)$'); plan_code:str; amount:int=Field(gt=0,le=10000000); currency:str='INR'
@router.post('/checkout',status_code=201)
def checkout(data:CheckoutIn,user:User=Depends(company_user),db:Session=Depends(get_db)):
    if data.provider=='razorpay':
        if not RAZORPAY_KEY_ID or not RAZORPAY_KEY_SECRET: raise HTTPException(503,'Razorpay is not configured')
        try:
            import razorpay
            client=razorpay.Client(auth=(RAZORPAY_KEY_ID,RAZORPAY_KEY_SECRET))
            order=client.order.create({'amount':data.amount,'currency':data.currency.upper(),'receipt':f'company-{user.company_id}-{data.plan_code}'})
        except Exception as exc: raise HTTPException(502,f'Razorpay order creation failed: {exc}')
        row=Subscription(company_id=user.company_id,provider='razorpay',provider_subscription_id=order['id'],plan_code=data.plan_code,status='pending',amount=data.amount/100,currency=data.currency.upper())
        db.add(row); db.commit(); return {'provider':'razorpay','key_id':RAZORPAY_KEY_ID,'order':order}
    if not STRIPE_SECRET_KEY: raise HTTPException(503,'Stripe is not configured')
    try:
        import stripe
        stripe.api_key=STRIPE_SECRET_KEY
        session=stripe.checkout.Session.create(mode='payment',line_items=[{'price_data':{'currency':data.currency.lower(),'product_data':{'name':data.plan_code},'unit_amount':data.amount},'quantity':1}],success_url='http://localhost:5173/billing/success?session_id={CHECKOUT_SESSION_ID}',cancel_url='http://localhost:5173/billing/cancel')
    except Exception as exc: raise HTTPException(502,f'Stripe checkout creation failed: {exc}')
    row=Subscription(company_id=user.company_id,provider='stripe',provider_subscription_id=session.id,plan_code=data.plan_code,status='pending',amount=data.amount/100,currency=data.currency.upper()); db.add(row); db.commit()
    return {'provider':'stripe','checkout_url':session.url,'session_id':session.id}
@router.get('/subscriptions')
def subscriptions(user:User=Depends(company_user),db:Session=Depends(get_db)):
    return db.query(Subscription).filter_by(company_id=user.company_id).order_by(Subscription.id.desc()).all()
@router.post('/webhooks/razorpay')
async def razorpay_webhook(request:Request,db:Session=Depends(get_db)):
    body=await request.body(); signature=request.headers.get('x-razorpay-signature','')
    if not RAZORPAY_WEBHOOK_SECRET: raise HTTPException(503,'Webhook secret is not configured')
    expected=hmac.new(RAZORPAY_WEBHOOK_SECRET.encode(),body,hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature,expected): raise HTTPException(400,'Invalid webhook signature')
    event=json.loads(body); entity=event.get('payload',{}).get('payment',{}).get('entity',{}); order_id=entity.get('order_id')
    if order_id:
        row=db.query(Subscription).filter_by(provider='razorpay',provider_subscription_id=order_id).first()
        if row: row.status='active' if event.get('event')=='payment.captured' else row.status; db.commit()
    return {'received':True}
@router.post('/webhooks/stripe')
async def stripe_webhook(request:Request,db:Session=Depends(get_db)):
    if not STRIPE_WEBHOOK_SECRET: raise HTTPException(503,'Webhook secret is not configured')
    try:
        import stripe
        event=stripe.Webhook.construct_event(await request.body(),request.headers.get('stripe-signature',''),STRIPE_WEBHOOK_SECRET)
    except Exception: raise HTTPException(400,'Invalid Stripe webhook')
    if event['type']=='checkout.session.completed':
        sid=event['data']['object']['id']; row=db.query(Subscription).filter_by(provider='stripe',provider_subscription_id=sid).first()
        if row: row.status='active'; db.commit()
    return {'received':True}
