package com.nicheexplorer.apiserver.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = "*")
public class ArxivProxyController {

    private final RestTemplate restTemplate = new RestTemplate();

    @Value("${genai.base-url}")
    private String genaiBaseUrl;

    @GetMapping("/arxiv-categories")
    public ResponseEntity<?> getCategories() {
        String url = genaiBaseUrl + "/arxiv/categories";
        return restTemplate.getForEntity(url, Object.class);
    }

    @PostMapping("/build-advanced-query")
    public ResponseEntity<?> buildQuery(@RequestBody Map<String, Object> body) {
        String url = genaiBaseUrl + "/arxiv/build-query";
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<Map<String, Object>> entity = new HttpEntity<>(body, headers);
        return restTemplate.postForEntity(url, entity, Object.class);
    }
} 