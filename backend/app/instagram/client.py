import instaloader
from ..models.schemas import InstagramProfile
from typing import Optional

class InstagramClient:
    def __init__(self):
        self.L = instaloader.Instaloader(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    def get_profile(self, username: str) -> Optional[InstagramProfile]:
        try:
            # Note: For production, you might need to login to avoid rate limits
            # but for public data, sometimes it works without.
            # We'll handle errors gracefully as requested.
            profile = instaloader.Profile.from_username(self.L.context, username)
            
            recent_posts = []
            if not profile.is_private:
                # Get last 5 posts for analysis
                count = 0
                for post in profile.get_posts():
                    if count >= 5:
                        break
                    recent_posts.append({
                        "caption": post.caption if post.caption else "",
                        "url": post.url,
                        "timestamp": post.date_utc.isoformat()
                    })
                    count += 1

            return InstagramProfile(
                username=profile.username,
                display_name=profile.full_name or "Unavailable",
                bio=profile.biography or "Unavailable",
                profile_pic_url=profile.profile_pic_url or "Unavailable",
                is_private=profile.is_private,
                follower_count=profile.followers,
                following_count=profile.followees,
                post_count=profile.mediacount,
                recent_posts=recent_posts,
                access_status="Private" if profile.is_private else "Public"
            )
        except Exception as e:
            print(f"Error retrieving Instagram profile: {e}")
            return None
