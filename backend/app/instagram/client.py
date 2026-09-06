import logging
from typing import Optional

import instaloader

from ..models.schemas import InstagramProfile

logger = logging.getLogger("sonics.instagram")


class InstagramClient:
    """Read-only fetcher for public Instagram profiles and recent posts.

    Retrieves only information that is legitimately exposed to the public
    (profile fields plus captions/URLs of the most recent posts). No login,
    no private data, no posting/reporting.
    """

    def __init__(self):
        self.L = instaloader.Instaloader(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        )

    def get_profile(self, username: str) -> Optional[InstagramProfile]:
        try:
            profile = instaloader.Profile.from_username(self.L.context, username)

            recent_posts = []
            if not profile.is_private:
                # Get the most recent posts (public) for content analysis.
                count = 0
                for post in profile.get_posts():
                    if count >= 5:
                        break
                    recent_posts.append(
                        {
                            "caption": post.caption if post.caption else "",
                            "url": post.url,
                            "timestamp": post.date_utc.isoformat(),
                        }
                    )
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
                access_status="Private" if profile.is_private else "Public",
            )
        except Exception as e:  # instaloader raises many error types; report and degrade
            logger.warning("Could not retrieve Instagram profile for '%s': %s", username, e)
            return None
