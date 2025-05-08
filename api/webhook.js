export default function handler(request) {
  const url = new URL(request.url);
  const params = new URLSearchParams(url.search);
  
  // Agregar logs para depuración
  console.log(`Método: ${request.method}`);
  console.log(`URL: ${request.url}`);
  
  if (request.method === 'GET') {
    const mode = params.get('hub.mode');
    const token = params.get('hub.verify_token');
    const challenge = params.get('hub.challenge');
    
    const verifyToken = '8a4c9e2f7b3d1a5c8e4f2a169c7e5e3f';
    
    console.log(`Mode: ${mode}`);
    console.log(`Token recibido: ${token}`);
    console.log(`Challenge: ${challenge}`);
    console.log(`Token esperado: ${verifyToken}`);
    
    if (mode === 'subscribe' && token === verifyToken) {
      console.log('WEBHOOK_VERIFIED');
      return new Response(challenge, { status: 200 });
    } else {
      console.log('Verification failed');
      return new Response('Verification failed', { status: 403 });
    }
  }
  
  if (request.method === 'POST') {
    console.log('Recibida notificación POST');
    return new Response('OK', { status: 200 });
  }
  
  return new Response('Method not allowed', { status: 405 });
}
