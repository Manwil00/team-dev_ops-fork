package com.nicheexplorer.apiserver;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import com.nicheexplorer.apiserver.config.GenAiProperties;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication(scanBasePackages = "com.nicheexplorer.apiserver")
@EnableConfigurationProperties(GenAiProperties.class)
@EntityScan(basePackages = "com.nicheexplorer.apiserver.model")
public class ApiServerApplication {
    
    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
    
    public static void main(String[] args) {
        SpringApplication.run(ApiServerApplication.class, args);
    }
} 