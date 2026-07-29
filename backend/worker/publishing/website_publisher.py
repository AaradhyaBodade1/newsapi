def publish_to_website(generated_post_id: str) -> str:
    """'Publishing' to the website has no external API — the public Next.js
    site queries `generated_posts` directly via Supabase (anon key, RLS
    restricted to status='published'), so flipping the post's status (done by
    the orchestrator once every platform's publish_jobs row succeeds) is the
    entire act of publishing. This function exists so the website behaves
    like every other platform in the publish_jobs bookkeeping loop."""
    return generated_post_id
