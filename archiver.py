import pandas as pd
import pdfkit
import scraper

class Archiver:
    def __init__(self, api_key):
        self.api_key = api_key
        self.channels = {}

    def add_channel(self, channel_id):
        """Adds a new channel to the archive."""
        if channel_id not in self.channels:
            self.channels[channel_id] = scraper.Scraper(channel_id, self.api_key)

    def update_stats(self):
        """Updates the statistics for all channels."""
        data = []
        for channel_id, channel in self.channels.items():
            total_duration = channel.get_total_duration()
            watched_duration = channel.get_watched_duration()
            unwatched_duration = channel.get_unwatched_duration()
            watched_percentage = channel.get_watched_percentage()
            unwatched_percentage = channel.get_unwatched_percentage()
            data.append({
                "Channel ID": channel_id,
                "Total Duration": total_duration,
                "Watched Duration": watched_duration,
                "Unwatched Duration": unwatched_duration,
                "Watched Percentage": watched_percentage,
                "Unwatched Percentage": unwatched_percentage
            })
        self.df = pd.DataFrame(data)

    def save_report(self, filename):
        """Generates a PDF report with the statistics for all channels."""
        self.update_stats()
        html = self.df.to_html(index=False, justify="center")
        options = {
            "page-size": "A4",
            "margin-top": "1cm",
            "margin-right": "1cm",
            "margin-bottom": "1cm",
            "margin-left": "1cm",
        }
        pdfkit.from_string(html, filename, options=options)

    def mark_as_watched(self, channel_id, video_id):
        """Marks a video as watched and updates the archive."""
        self.channels[channel_id].mark_as_watched(video_id)

    def mark_as_unwatched(self, channel_id, video_id):
        """Marks a video as unwatched and updates the archive."""
        self.channels[channel_id].mark_as_unwatched(video_id)