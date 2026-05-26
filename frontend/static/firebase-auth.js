// OTP Authentication

async function sendOTP() {
    const phoneNumber = document.getElementById('otpPhone').value;
    
    try {
        const response = await fetch('/api/send_otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone: phoneNumber })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert("OTP Sent Successfully!");
            window.location.href = "/verify_otp_page";
        } else {
            alert("Failed to send OTP: " + data.message);
        }
    } catch (error) {
        console.error("Error sending OTP", error);
        alert("Failed to send OTP: " + error.message);
    }
}

async function verifyOTP() {
    const code = document.getElementById('otpCode').value;
    
    try {
        const response = await fetch('/api/verify_otp', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });
        
        const data = await response.json();
        if (data.success) {
            window.location.href = data.redirect;
        } else {
            alert("Login failed: " + data.message);
        }
    } catch (error) {
        console.error("Error verifying OTP", error);
        alert("Invalid OTP code.");
    }
}

window.sendOTP = sendOTP;
window.verifyOTP = verifyOTP;
