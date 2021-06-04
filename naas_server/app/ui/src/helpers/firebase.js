import firebase from "firebase/app";
import "firebase/auth";
import "firebase/firestore";
import "firebase/storage";

const liveConfig = {
  apiKey: "AIzaSyDigZvzsF-bdsrr9YnfW967eFqfr_in5Zk",
  authDomain: "narupa-web-ui.firebaseapp.com",
  projectId: "narupa-web-ui",
  storageBucket: "narupa-web-ui.appspot.com",
  messagingSenderId: "467879059099",
  appId: "1:467879059099:web:3be0b8a2b6c775c2b6f03e"
};
const betaConfig = {
  apiKey: "AIzaSyAZXsHvApXKwAMOr0w4UU33XZQKFypB2NA",
  authDomain: "narupa-web-ui-beta.firebaseapp.com",
  projectId: "narupa-web-ui-beta",
  storageBucket: "narupa-web-ui-beta.appspot.com",
  messagingSenderId: "526461332746",
  appId: "1:526461332746:web:bb8ca37b69cdc116765ef3"
};

const isLive = window.location.hostname === 'app.narupa.xyz';

firebase.initializeApp(isLive ? liveConfig : betaConfig);

export const fireauth = firebase.auth;
export const firestore = firebase.firestore;
export const firestorage = firebase.storage;

export const firebaseGoogleProvider = () => {
  return new firebase.auth.GoogleAuthProvider();
};
