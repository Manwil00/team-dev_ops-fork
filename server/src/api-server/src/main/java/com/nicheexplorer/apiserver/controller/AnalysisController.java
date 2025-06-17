package com.nicheexplorer.apiserver.controller;

import com.nicheexplorer.apiserver.dto.AnalyzeRequest;
import com.nicheexplorer.apiserver.dto.AnalysisResponse;
import com.nicheexplorer.apiserver.service.AnalysisService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@CrossOrigin
@RestController
@RequestMapping("/api")
public class AnalysisController {

    private final AnalysisService analysisService;

    public AnalysisController(AnalysisService analysisService) {
        this.analysisService = analysisService;
    }

    @PostMapping("/analyze")
    public ResponseEntity<AnalysisResponse> analyze(@RequestBody AnalyzeRequest request) {
        if (request.getQuery() == null || request.getQuery().trim().isEmpty()) {
            return ResponseEntity.badRequest().build();
        }
        AnalysisResponse response = analysisService.analyze(request);
        return ResponseEntity.ok(response);
    }
} 