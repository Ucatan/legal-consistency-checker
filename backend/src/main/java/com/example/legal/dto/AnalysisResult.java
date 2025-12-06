package com.example.legal.dto;

import lombok.Data;
import java.util.List;

@Data
public class AnalysisResult {
    private String document;
    private List<Issue> issues;
    private String status = "completed";

    @Data
    public static class Issue {
        private String type;
        private String description;
        private String location;
        private String severity;
//        private String severity = "medium";
    }
}