import axios from 'axios';
import { fireauth } from './firebase';

const BASE_API_URL = process.env.NODE_ENV === 'development' ? 'http://localhost:5000' : 'https://app.narupa.xyz'

export async function createUser(firebaseUser, displayName) {
  const { email, uid } = firebaseUser;
  const name = displayName || firebaseUser.displayName
  const data = { email, firebase_uid: uid, name };
  return _post(`${BASE_API_URL}/api/users`, data);
}

export async function getMe() {
  return _get(`${BASE_API_URL}/api/users/me`);
}

export async function updateMeZoom(zoom_authorization_code) {
  return _put(`${BASE_API_URL}/api/users/me/zoom`, { zoom_authorization_code });
}

export async function getSessions() {
  return _get(`${BASE_API_URL}/api/sessions`);
}

export async function getSession(sessionId) {
  return _get(`${BASE_API_URL}/api/sessions/${sessionId}`);
}

export async function createSession(session) {
  return _post(`${BASE_API_URL}/api/sessions`, session);
}

export async function updateSession(session) {
  return _put(`${BASE_API_URL}/api/sessions/${session.id}`, session);
}

export async function deleteSession(sessionId) {
  return _delete(`${BASE_API_URL}/api/sessions/${sessionId}`);
}

export async function getSimulations() {
  return _get(`${BASE_API_URL}/api/simulations`);
}

export async function getSimulation(simulationId) {
  return _get(`${BASE_API_URL}/api/simulations/${simulationId}`);
}

export async function createSimulation(simulation) {
  return _post(`${BASE_API_URL}/api/simulations`, simulation);
}

export async function updateSimulation(simulation) {
  return _put(`${BASE_API_URL}/api/simulations/${simulation.id}`, simulation);
}

export async function deleteSimulation(simulationId) {
  return _delete(`${BASE_API_URL}/api/simulations/${simulationId}`);
}

async function _get(url) {
  const response = await axios.get(url, await headers());
  return response.data;
}

async function _post(url, data) {
  return await axios.post(url, JSON.stringify(data), await headers());
}

async function _put(url, data) {
  return await axios.put(url, JSON.stringify(data), await headers());
}

async function _delete(url) {
  return await axios.delete(url, await headers());
}

async function headers() {
  const idToken = await getIdToken();
  return { headers: { 'x-narupa-id-token': idToken, 'Content-Type': 'application/json' }};
}

async function getIdToken() {
  return await fireauth().currentUser.getIdToken();
}
