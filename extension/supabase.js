const SUPABASE_URL = 'https://fwdvbffemldsiustobyd.supabase.co'
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ3ZHZiZmZlbWxkc2l1c3RvYnlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzgzMzUzNDksImV4cCI6MjA1MzkxMTM0OX0.Nud4_Aqz9xsTRs6ZXzbkHSZK9IzcSElH4j6AacS9Z1Q'

class SupabaseClient {
  constructor() {
    this.supabase = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY)
  }

  async signUp(email, password) {
    const { data, error } = await this.supabase.auth.signUp({
      email,
      password,
    })
    return { data, error }
  }

  async signIn(email, password) {
    const { data, error } = await this.supabase.auth.signInWithPassword({
      email,
      password,
    })
    return { data, error }
  }

  async signOut() {
    const { error } = await this.supabase.auth.signOut()
    return { error }
  }

  async getSession() {
    const { data: { session }, error } = await this.supabase.auth.getSession()
    return { session, error }
  }
}

const supabaseClient = new SupabaseClient()
