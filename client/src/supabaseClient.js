/**
 * Supabase Client — single instance for auth + database.
 */
import { createClient } from '@supabase/supabase-js';

const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL || 'https://muzgtcplkqwswstewoyv.supabase.co';
const SUPABASE_ANON_KEY = process.env.REACT_APP_SUPABASE_ANON_KEY || 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im11emd0Y3Bsa3F3c3dzdGV3b3l2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwNjUxMzgsImV4cCI6MjA4ODY0MTEzOH0.76CBNNQt4jWQMKrots1yisTwonmIHLXSU-8O8THEAnU';

export const supabase = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
export { SUPABASE_URL, SUPABASE_ANON_KEY };
