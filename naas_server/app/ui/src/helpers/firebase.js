import firebase from "firebase/app";
import "firebase/auth";
import "firebase/firestore";
import "firebase/storage";

const firebaseConfig = {
	apiKey: "AIzaSyDfcNd-uiKYT75yJnYgz4ul7Y_JOWuRkEo",
	authDomain: "narupa-as-a-service.firebaseapp.com",
	databaseURL: "https://narupa-as-a-service.firebaseio.com",
	projectId: "narupa-as-a-service",
	storageBucket: "narupa-as-a-service.appspot.com",
	messagingSenderId: "765297605767",
	appId: "1:765297605767:web:096339fec51d165b054c22",
	measurementId: "G-WGGPGJ7HDF"
};


firebase.initializeApp(firebaseConfig);

export const fireauth = firebase.auth;
export const firestore = firebase.firestore;
export const firestorage = firebase.storage;

export const firebaseGoogleProvider = () => {
  return new firebase.auth.GoogleAuthProvider();
};
