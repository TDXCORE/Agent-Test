import { NextResponse } from 'next/server';
import { supabaseAdmin } from '@/lib/supabaseClient';

export const dynamic = 'force-static';

export async function GET() {
  try {
    // Get all users from Supabase
    const { data, error } = await supabaseAdmin
      .from('users')
      .select('id, full_name, phone, email, company, created_at');
    
    if (error) {
      console.error('Error fetching users:', error);
      return NextResponse.json({ error: error.message }, { status: 500 });
    }
    
    // Transform data for frontend
    const contacts = data.map(user => ({
      id: user.id,
      name: user.full_name,
      // Generate avatar data (since it's not in the schema)
      avatar: {
        type: "init",
        variant: "primary", // Can randomize this based on user.id
        title: user.full_name ? user.full_name.charAt(0).toUpperCase() : 'U'
      },
      status: "offline", // Default status
      lastChat: "Click to start conversation",
      time: new Date(user.created_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}),
      unread: 0
    }));
    
    return NextResponse.json(contacts);
  } catch (error) {
    console.error('Error in users API:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}
