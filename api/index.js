export default function handler(request) {
  return new Response("Webhook para WhatsApp Business API. Usa /webhook para la verificación.", {
    status: 200,
    headers: {
      "Content-Type": "text/plain"
    }
  });
}
