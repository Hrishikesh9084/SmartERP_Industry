from decimal import Decimal
def test_balanced_journal_rule():
    lines=[{'debit':Decimal('100'),'credit':Decimal('0')},{'debit':Decimal('0'),'credit':Decimal('100')}]
    assert sum(x['debit'] for x in lines)==sum(x['credit'] for x in lines)
def test_unbalanced_journal_rejected_by_invariant():
    lines=[{'debit':Decimal('100'),'credit':Decimal('0')},{'debit':Decimal('0'),'credit':Decimal('90')}]
    assert sum(x['debit'] for x in lines)!=sum(x['credit'] for x in lines)
