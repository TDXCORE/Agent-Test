import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseClient';

export const dynamic = 'force-static';

export async function GET(request) {
  try {
    // Get conversation_id from query params
    const { searchParams } = new URL(request.url);
    const conversation_id = searchParams.get('conversation_id');
    
    if (!conversation_id) {
      return NextResponse.json({ error: 'conversation_id is required' }, { status: 400 });
    }
    
    // Get all messages for the conversation
    const { data, error } = await supabaseAdmin
      .from('messages')
      .select('*')
      .eq('conversation_id', conversation_id)
      .order('created_at', { ascending: true });
    
    if (error) {
      console.error('Error fetching messages:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    // Transform data for frontend
    const messages = data.map(message => ({
      id: message.id,
      types: message.role === 'user' ? 'sent' : 'received',
      text: message.content,
      time: new Date(message.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      message_type: message.message_type,
      media_url: message.media_url
    }));
    
    return NextResponse.json(messages);
  } catch (error) {
    console.error('Error in messages API:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { conversation_id, content, message_type = 'text', media_url } = body;
    
    if (!conversation_id || !content) {
      return NextResponse.json({ error: 'conversation_id and content are required' }, { status: 400 });
    }
    
    // Add message to the conversation
    const { data, error } = await supabaseAdmin
      .from('messages')
      .insert({
        conversation_id,
        role: 'user', // Messages from the web interface are always from the user
        content,
        message_type,
        media_url
      })
      .select();
    
    if (error) {
      console.error('Error creating message:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    // Transform for frontend
    const message = {
      id: data[0].id,
      types: 'sent',
      text: data[0].content,
      time: new Date(data[0].created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      message_type: data[0].message_type,
      media_url: data[0].media_url
    };
    
    return NextResponse.json(message, { status: 201 });
  } catch (error) {
    console.error('Error in messages API:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
