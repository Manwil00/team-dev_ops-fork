package com.nicheexplorer.apiserver.service;

import com.rometools.rome.feed.synd.SyndEntry;
import com.rometools.rome.feed.synd.SyndFeed;
import com.rometools.rome.io.SyndFeedInput;
import com.rometools.rome.io.XmlReader;
import org.springframework.stereotype.Service;

import java.net.URL;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

/**
 * Small helper that downloads an RSS/Atom feed and returns the newest entries.
 */
@Service
public class FeedFetchService {

    public List<SyndEntry> fetch(String feedUrl, int limit) {
        try {
            URL url = new URL(feedUrl);
            SyndFeed feed = new SyndFeedInput().build(new XmlReader(url));
            return feed.getEntries().stream()
                    .limit(limit)
                    .collect(Collectors.toList());
        } catch (Exception e) {
            return Collections.emptyList();
        }
    }
} 