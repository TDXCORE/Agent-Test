import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseClient';

export const dynamic = 'force-static';

export async function GET(request) {
  try {
    // Get user_id from query params
    const { searchParams } = new URL(request.url);
    const user_id = searchParams.get('user_id');
    
    if (!user_id) {
      return NextResponse.json({ error: 'user_id is required' }, { status: 400 });
    }
    
    // Get all conversations for the user
    const { data, error } = await supabaseAdmin
      .from('conversations')
      .select(`
        id, 
        external_id, 
        platform, 
        status, 
        created_at,
        updated_at
      `)
      .eq('user_id', user_id)
      .eq('status', 'active');
    
    if (error) {
      console.error('Error fetching conversations:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('Error in conversations API:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST(request) {
  try {
    const body = await request.json();
    const { user_id, external_id, platform = 'web' } = body;
    
    if (!user_id || !external_id) {
      return NextResponse.json({ error: 'user_id and external_id are required' }, { status: 400 });
    }
    
    // Create a new conversation
    const { data, error } = await supabaseAdmin
      .from('conversations')
      .insert({
        user_id,
        external_id,
        platform,
        status: 'active'
      })
      .select();
    
    if (error) {
      console.error('Error creating conversation:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    return NextResponse.json(data[0], { status: 201 });
  } catch (error) {
    console.error('Error in conversations API:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
