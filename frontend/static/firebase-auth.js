// Firebase Configuration
const firebaseConfig = {
    apiKey: "AIzaSyDS8J7KX8ie_ILsixNNjPCDDx9_lZO7ej4",
    authDomain: "nearbypricefinder.firebaseapp.com",
    projectId: "nearbypricefinder",
    storageBucket: "nearbypricefinder.firebasestorage.app",
    messagingSenderId: "281104604927",
    appId: "1:281104604927:web:735713aca520e8848836ca",
    measurementId: "G-RG6JB3SP1D"
};

// Initialize Firebase
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, RecaptchaVerifier, signInWithPhoneNumber } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

const app = initializeApp(firebaseConfig);
const auth = getAuth(app);

window.recaptchaVerifier = new RecaptchaVerifier(auth, 'recaptcha-container', {
    'size': 'invisible',
    'callback': (response) => {
        // reCAPTCHA solved, allow signInWithPhoneNumber.
    }
});

async function sendOTP() {
    const phoneNumber = document.getElementById('otpPhone').value;
    const appVerifier = window.recaptchaVerifier;

    try {
        const confirmationResult = await signInWithPhoneNumber(auth, phoneNumber, appVerifier);
        window.confirmationResult = confirmationResult;
        alert("OTP Sent Successfully!");
        // Redirect to verify page or show code input
        window.location.href = "/verify_otp_page";
    } catch (error) {
        console.error("Error sending OTP", error);
        alert("Failed to send OTP: " + error.message);
    }
}

async function verifyOTP() {
    const code = document.getElementById('otpCode').value;
    
    try {
        const result = await window.confirmationResult.confirm(code);
        const user = result.user;
        const idToken = await user.getIdToken();
        
        // Send token to backend to create session
        const response = await fetch('/firebase_login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id_token: idToken })
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
