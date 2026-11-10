const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(
  /\/$/,
  ""
);

export const sendMobileLoginOTP = async (phoneNumber) => {
  const response = await fetch(
    `${API_URL}/api/auth/phone/send-otp`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        phone_number: phoneNumber,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "Unable to send OTP");
  }

  return data;
};


export const verifyMobileLoginOTP = async (phoneNumber, otp) => {
  const response = await fetch(
    `${API_URL}/api/auth/phone/verify-otp`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        phone_number: phoneNumber,
        otp: otp,
      }),
    }
  );

  const data = await response.json();

  if (!response.ok) {
    throw new Error(data.detail || "OTP verification failed");
  }

  localStorage.setItem("access_token", data.access_token);

  return data;
};