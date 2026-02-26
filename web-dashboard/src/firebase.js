import { initializeApp } from "firebase/app";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
    apiKey: "AIzaSyBh0ixrz9yXbE0PYeP2caFzB2h5tTMqvuw",
    authDomain: "linkedin-automission.firebaseapp.com",
    projectId: "linkedin-automission",
    storageBucket: "linkedin-automission.firebasestorage.app",
    messagingSenderId: "668923810815",
    appId: "1:668923810815:web:c65d3434a7992e3ea88dca",
    measurementId: "G-PNP8S1F07H"
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
