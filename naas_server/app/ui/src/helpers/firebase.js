import firebase from "firebase/app";
import "firebase/auth";
import "firebase/firestore";
import "firebase/storage";

const firebaseConfig = {
  apiKey: "AIzaSyDigZvzsF-bdsrr9YnfW967eFqfr_in5Zk",
  authDomain: "narupa-web-ui.firebaseapp.com",
  databaseURL: "https://narupa-web-ui.firebaseio.com",
  projectId: "narupa-web-ui",
  storageBucket: "narupa-web-ui.appspot.com",
  messagingSenderId: "467879059099",
  appId: "1:467879059099:web:3be0b8a2b6c775c2b6f03e"
};


firebase.initializeApp(firebaseConfig);

export const fireauth = firebase.auth;
export const firestore = firebase.firestore;
export const firestorage = firebase.storage;

export const firebaseGoogleProvider = () => {
  return new firebase.auth.GoogleAuthProvider();
};
