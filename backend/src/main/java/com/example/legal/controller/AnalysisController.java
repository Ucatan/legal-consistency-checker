package com.example.legal.controller;

import com.example.legal.dto.AnalysisResult;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

@RestController
@RequestMapping("/api")
public class AnalysisController {

    private final WebClient nlpClient;

    public AnalysisController(@Value("${nlp.service.url:http://localhost:8000}") String nlpUrl) {
        this.nlpClient = WebClient.builder()
                .baseUrl(nlpUrl)
                .build();
    }

    @PostMapping(value = "/analyze", consumes = MediaType.MULTIPART_FORM_DATA_VALUE)
    public Mono<ResponseEntity<AnalysisResult>> analyze(@RequestPart("file") MultipartFile file) {
        try {
            // Подготавливаем multipart/form-data
            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            });

            return nlpClient.post()
                    .uri("/analyze")
                    .contentType(MediaType.MULTIPART_FORM_DATA)
                    .bodyValue(body)
                    .retrieve()
                    .toEntity(AnalysisResult.class)
                    .onErrorResume(error -> Mono.just(ResponseEntity.badRequest().build()));
        } catch (Exception e) {
            return Mono.just(ResponseEntity.badRequest().build());
        }
    }
}