import { fireauth, firebaseGoogleProvider } from './firebase';

export async function register(email, password) {
  return await fireauth().createUserWithEmailAndPassword(email, password);
}

export async function logout()  {
  return await fireauth().signOut()
}

export async function login(email, password) {
  return await fireauth().signInWithEmailAndPassword(email, password)
}

export async function loginWithGoogle() {
  return await fireauth().signInWithPopup(firebaseGoogleProvider());
}