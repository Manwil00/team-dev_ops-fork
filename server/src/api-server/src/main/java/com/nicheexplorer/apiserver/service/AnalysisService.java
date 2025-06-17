package com.nicheexplorer.apiserver.service;

import com.nicheexplorer.apiserver.dto.AnalyzeRequest;
import com.nicheexplorer.apiserver.dto.AnalysisResponse;
import com.nicheexplorer.apiserver.dto.TrendDto;
import com.nicheexplorer.apiserver.dto.ArticleDto;
import com.rometools.rome.feed.synd.SyndEntry;
import org.springframework.stereotype.Service;
import com.nicheexplorer.apiserver.service.SourceClassificationClient.ClassificationResponse;
import java.util.stream.Stream;
import com.nicheexplorer.apiserver.service.TrendExplainClient;
import com.nicheexplorer.apiserver.service.FeedFetchService;

import java.time.Instant;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.stream.Collectors;

@Service
public class AnalysisService {

    private static final Set<String> STOP_WORDS = new HashSet<>(Arrays.asList(
            "the", "and", "of", "in", "to", "for", "a", "on", "with", "by", "an", "from", "at", "is", "as", "are", "be", "this", "that", "it", "we", "our", "using", "based"));

    private final AtomicInteger idGenerator = new AtomicInteger();
    private final SourceClassificationClient classifier;
    private final TrendExplainClient explainClient;
    private final FeedFetchService feedFetch;

    public AnalysisService(SourceClassificationClient classifier,
                           TrendExplainClient explainClient,
                           FeedFetchService feedFetch) {
        this.classifier = classifier;
        this.explainClient = explainClient;
        this.feedFetch = feedFetch;
    }

    public AnalysisResponse analyze(AnalyzeRequest request) {
        ClassificationResponse cls = classifier.classify(request.getQuery());
        String type = cls != null && "community".equalsIgnoreCase(cls.source()) ? "Community" : "Research";
        String feedId = cls != null ? cls.feed() : (type.equals("Research") ? "cs.CV" : "computervision");
        String feedUrl = type.equals("Research") ? "https://rss.arxiv.org/rss/" + feedId : "https://www.reddit.com/r/" + feedId + ".rss";

        List<SyndEntry> entries = feedFetch.fetch(feedUrl, request.getMaxArticles());
        Map<String, Integer> keywordCounts = extractKeywords(entries);
        Map<String, List<ArticleDto>> keywordArticles = mapArticlesForKeywords(entries);

        // Select top N keywords as trends
        List<TrendDto> trends = keywordCounts.entrySet().stream()
                .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
                .limit(request.getTrendClusters())
                .map(entry -> new TrendDto(
                        UUID.randomUUID().toString(),
                        entry.getKey(),
                        explainClient.explain(entry.getKey(), keywordArticles.getOrDefault(entry.getKey(), Collections.emptyList())
                                .stream().map(ArticleDto::getTitle).toList()),
                        entry.getValue(),
                        Math.min(100, entry.getValue() * 5),
                        keywordArticles.getOrDefault(entry.getKey(), Collections.emptyList())))
                .collect(Collectors.toList());

        return new AnalysisResponse(
                String.valueOf(idGenerator.incrementAndGet()),
                request.getQuery(),
                Instant.now(),
                type,
                trends,
                feedUrl);
    }

    private Map<String, Integer> extractKeywords(List<SyndEntry> entries) {
        Map<String, Integer> counts = new HashMap<>();
        Pattern pattern = Pattern.compile("[A-Za-z]{3,}");
        for (SyndEntry entry : entries) {
            String text = entry.getTitle() + " " + (entry.getDescription() != null ? entry.getDescription().getValue() : "");
            Matcher matcher = pattern.matcher(text.toLowerCase());
            while (matcher.find()) {
                String word = matcher.group();
                if (STOP_WORDS.contains(word)) continue;
                counts.put(word, counts.getOrDefault(word, 0) + 1);
            }
        }
        return counts;
    }

    private Map<String, List<ArticleDto>> mapArticlesForKeywords(List<SyndEntry> entries) {
        Map<String, List<ArticleDto>> map = new HashMap<>();
        for (SyndEntry entry : entries) {
            String content = (entry.getTitle() + " " + (entry.getDescription() != null ? entry.getDescription().getValue() : "")).toLowerCase();
            for (String word : STOP_WORDS) {
                // skip stop words
            }
            // tokenize simple
            for (String token : content.split("\\W+")) {
                if (token.length() < 3 || STOP_WORDS.contains(token)) continue;
                List<ArticleDto> list = map.computeIfAbsent(token, k -> new ArrayList<>());
                if (list.size() >= 3) continue; // limit
                list.add(new ArticleDto(UUID.randomUUID().toString(), entry.getTitle(), entry.getLink(), entry.getDescription()!=null? entry.getDescription().getValue():""));
            }
        }
        return map;
    }
} 