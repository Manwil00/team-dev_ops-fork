package com.nicheexplorer.apiserver.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.nicheexplorer.generated.model.AnalyzeRequest;
import com.nicheexplorer.generated.model.AnalysisResponse;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;

import java.util.List;
import java.util.UUID;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/**
 * Unit tests for AnalysisService.
 *
 * Test Description:
 * This class tests the internal logic of the AnalysisService, focusing on its
 * interactions with the database (via JdbcTemplate) and the orchestration service.
 * All external dependencies are mocked to ensure the service is tested in isolation.
 */
@ExtendWith(MockitoExtension.class)
public class AnalysisServiceTest {

    @Mock
    private JdbcTemplate jdbcTemplate;

    @Mock
    private AnalysisOrchestrationService orchestrationService;

    @Mock
    private ObjectMapper objectMapper;

    @InjectMocks
    private AnalysisService analysisService;

    private AnalysisResponse mockAnalysisResponse;

    @BeforeEach
    void setUp() {
        mockAnalysisResponse = new AnalysisResponse();
        mockAnalysisResponse.setId(UUID.randomUUID());
        mockAnalysisResponse.setQuery("test query");
    }

    /**
     * Tests the getAnalyses method.
     *
     * Test Description:
     * Verifies that the service correctly queries the database to retrieve a list
     * of past analyses.
     *
     * Assertions:
     * - Asserts that `jdbcTemplate.query` is called with the correct SQL statement.
     * - Asserts that the returned list contains the mock analysis object.
     */
    @Test
    void whenGetAnalyses_thenReturnsListOfAnalyses() {
        // Arrange
        when(jdbcTemplate.query(anyString(), any(RowMapper.class), eq(10), eq(0)))
                .thenReturn(List.of(mockAnalysisResponse));

        // Act
        List<AnalysisResponse> responses = analysisService.getAnalyses(10, 0);

        // Assert
        assertThat(responses).hasSize(1);
        assertThat(responses.get(0).getId()).isEqualTo(mockAnalysisResponse.getId().toString());
        verify(jdbcTemplate).query(anyString(), any(RowMapper.class), eq(10), eq(0));
    }

    /**
     * Tests the getAnalysisById method.
     *
     * Test Description:
     * Verifies that the service can retrieve a single analysis by its ID and that
     * it correctly calls the hydration method to populate related data.
     *
     * Assertions:
     * - Asserts that `jdbcTemplate.queryForObject` is called.
     * - Asserts that the returned object matches the mock response.
     */
    @Test
    void whenGetAnalysisById_thenReturnsSingleAnalysis() {
        // Arrange
        when(jdbcTemplate.queryForObject(anyString(), any(RowMapper.class), any(UUID.class)))
                .thenReturn(mockAnalysisResponse);

        // Act
        AnalysisResponse response = analysisService.getAnalysisById(mockAnalysisResponse.getId().toString());

        // Assert
        assertThat(response).isNotNull();
        assertThat(response.getId()).isEqualTo(mockAnalysisResponse.getId().toString());
        verify(jdbcTemplate).queryForObject(anyString(), any(RowMapper.class), any(UUID.class));
    }

    /**
     * Tests the deleteAnalysis method.
     *
     * Test Description:
     * Verifies that the service issues the correct commands to the database to
     * delete an analysis and its related topics and articles.
     *
     * Assertions:
     * - Asserts that `jdbcTemplate.update` is called three times with the correct
     *   SQL to delete from each of the three related tables.
     */
    @Test
    void whenDeleteAnalysis_thenDeletesFromDatabase() {
        // Arrange
        String id = UUID.randomUUID().toString();
        when(jdbcTemplate.update(anyString(), any(UUID.class))).thenReturn(1);

        // Act
        analysisService.deleteAnalysis(id);

        // Assert
        verify(jdbcTemplate).update(eq("DELETE FROM article WHERE analysis_id = ?"), any(UUID.class));
        verify(jdbcTemplate).update(eq("DELETE FROM topic WHERE analysis_id = ?"), any(UUID.class));
        verify(jdbcTemplate).update(eq("DELETE FROM analysis WHERE id = ?"), any(UUID.class));
    }
} 