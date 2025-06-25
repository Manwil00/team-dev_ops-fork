package com.nicheexplorer.apiserver.controller;

import com.nicheexplorer.apiserver.dto.AnalysisResponse;
import com.nicheexplorer.apiserver.dto.AnalyzeRequest;
import com.nicheexplorer.apiserver.service.AnalysisService;
import org.springframework.web.bind.annotation.*;
import org.springframework.http.ResponseEntity;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class AnalysisController {

    private final AnalysisService analysisService;

    public AnalysisController(AnalysisService analysisService) {
        this.analysisService = analysisService;
    }

    @PostMapping("/analyze")
    public ResponseEntity<AnalysisResponse> analyze(@RequestBody AnalyzeRequest request) {
        try {
            AnalysisResponse response = analysisService.analyze(request);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            throw new RuntimeException("Failed to analyze query", e);
        }
    }

    @GetMapping("/analysis/history")
    public ResponseEntity<List<AnalysisResponse>> getHistory() {
        try {
            List<AnalysisResponse> history = analysisService.getAnalysisHistory(null, 20);
            return ResponseEntity.ok(history);
        } catch (Exception e) {
            throw new RuntimeException("Failed to get analysis history", e);
        }
    }

    @DeleteMapping("/analysis/{id}")
    public ResponseEntity<Void> deleteAnalysis(@PathVariable String id) {
        try {
            analysisService.deleteAnalysis(id);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            throw new RuntimeException("Failed to delete analysis", e);
        }
    }

    @PostMapping("/topic/{topicId}/embedding")
    public ResponseEntity<Map<String, Object>> getTopicEmbedding(@PathVariable String topicId) {
        try {
            Map<String, Object> embedding = analysisService.getTopicEmbedding(topicId);
            return ResponseEntity.ok(embedding);
        } catch (Exception e) {
            throw new RuntimeException("Failed to get topic embedding", e);
        }
    }

    @PostMapping("/article/{articleId}/embedding")
    public ResponseEntity<Map<String, Object>> getArticleEmbedding(@PathVariable String articleId) {
        try {
            Map<String, Object> embedding = analysisService.getArticleEmbedding(articleId);
            return ResponseEntity.ok(embedding);
        } catch (Exception e) {
            throw new RuntimeException("Failed to get article embedding", e);
        }
    }
} 