import firebase from "firebase/app";
import "firebase/auth";
import "firebase/firestore";
import "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyDLhkkakJyfkc-1-ZkMvMRZ3VYAtiuaxZQ",
  authDomain: "narupa-web.firebaseapp.com",
  databaseURL: "https://narupa-web.firebaseio.com",
  projectId: "narupa-web",
  storageBucket: "narupa-web.appspot.com",
  messagingSenderId: "877663772683",
  appId: "1:877663772683:web:2a3b60a776614ea05aa70e"
};

firebase.initializeApp(firebaseConfig);

export const fireauth = firebase.auth;
export const firestore = firebase.firestore;
export const firestorage = firebase.storage;

export const firebaseGoogleProvider = () => {
  return new firebase.auth.GoogleAuthProvider();
};