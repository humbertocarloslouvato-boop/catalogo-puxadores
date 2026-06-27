---
date: 2026-06-27T14:01:32.434610+00:00
project: ruflo-main
agent: kimi-code-cli
tags: ["video", "ffmpeg", "pattern", "ecommerce"]
summary: "Pipeline de vídeo com ffmpeg para e-commerce"
---

# Pipeline de vídeo com ffmpeg para e-commerce

Pipeline padrão para produzir vídeos de e-commerce: (1) criar abertura com logo via PIL + ffmpeg; (2) concatenar abertura com vídeo base usando anullsrc + concat em filter_complex; (3) aplicar melhorias de áudio (highpass, lowpass, afftdn, loudnorm, compressor, EQ); (4) gerar variações com ajustes seguros de cor/saturation/contraste + pitch shift sutil; (5) validar resolução/duração/codec; (6) extrair thumbnail e injetar metadata.
