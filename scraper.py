from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from oauth2client.tools import argparser
import json
import os
from datetime import timedelta


class Scraper:
    CACHE_DIR = "cache"

    def __init__(self, channel_id, api_key):
        self.channel_id = channel_id
        self.api_key = api_key
        self.youtube = build("youtube", "v3", developerKey=self.api_key)
        self.videos = self._get_channel_videos()

    def _get_channel_videos(self):
        """Retrieves all videos uploaded by the channel."""
        playlist_items = []
        next_page_token = None

        # check if cached data exists
        cache_file = os.path.join(self.CACHE_DIR, f"{self.channel_id}.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)

        # use pagination to retrieve all videos
        while True:
            res = self.youtube.playlistItems().list(
                part="contentDetails",
                maxResults=50,
                playlistId=f"UU{self.channel_id[2:]}",
                pageToken=next_page_token
            ).execute()

            playlist_items.extend(res["items"])
            next_page_token = res.get("nextPageToken")

            if not next_page_token:
                break

        # extract video ids from playlist items
        video_ids = [item["contentDetails"]["videoId"] for item in playlist_items]

        # retrieve video details
        videos = []
        for i in range(0, len(video_ids), 50):
            res = self.youtube.videos().list(
                part="snippet,contentDetails",
                id=",".join(video_ids[i:i+50])
            ).execute()
            videos.extend(res["items"])

        # cache the data
        with open(cache_file, "w") as f:
            json.dump(videos, f)

        return videos

    def _get_duration(self, video):
        """Converts YouTube video duration string to seconds."""
        duration = video["contentDetails"]["duration"]
        return timedelta(seconds=int(duration[2:].replace("H", ":").replace("M", ":").replace("S", "")))

    def _get_watched_ids(self):
        """Retrieves the list of watched video IDs from cache."""
        cache_file = os.path.join(self.CACHE_DIR, f"{self.channel_id}_watched.json")
        if os.path.exists(cache_file):
            with open(cache_file, "r") as f:
                return json.load(f)
        else:
            return []

    def _cache_watched_ids(self, watched_ids):
        """Caches the list of watched video IDs."""
        cache_file = os.path.join(self.CACHE_DIR, f"{self.channel_id}_watched.json")
        with open(cache_file, "w") as f:
            json.dump(watched_ids, f)

    def get_total_duration(self):
        """Returns the total duration of all videos in the channel."""
        return sum(self._get_duration(video).total_seconds() for video in self.videos)

    def get_watched_duration(self):
        """Returns the duration of watched videos in the channel."""
        watched_duration = 0
        watched_ids = self._get_watched_ids()
        for video in self.videos:
            if video["id"] in watched_ids:
                watched_duration += self._get_duration(video).total_seconds()
        return watched_duration

    def get_unwatched_duration(self):
        """Returns the duration of unwatched videos in the channel."""
        watched_duration = self.get_watched_duration()
        total_duration = self.get_total_duration()
        return total_duration - watched_duration

    def get_watched_percentage(self):
        """Returns the percentage of watched videos in the channel."""
        watched_duration = self.get_watched_duration()
        total_duration = self.get_total_duration()
        if total_duration > 0:
            return (watched_duration / total_duration) * 100
        else:
            return 0

    def get_unwatched_percentage(self):
        """Returns the percentage of unwatched videos in the channel."""
        unwatched_duration = self.get_unwatched_duration()
        total_duration = self.get_total_duration()
        if total_duration > 0:
            return (unwatched_duration / total_duration) * 100
        else:
            return 0

    def mark_as_watched(self, video_id):
        """Marks a video as watched and updates the cache."""
        watched_ids = self._get_watched_ids()
        if video_id not in watched_ids:
            watched_ids.append(video_id)
            self._cache_watched_ids(watched_ids)

    def mark_as_unwatched(self, video_id):
        """Marks a video as unwatched and updates the cache."""
        watched_ids = self._get_watched_ids()
        if video_id in watched_ids:
            watched_ids.remove(video_id)
            self._cache_watched_ids(watched_ids)