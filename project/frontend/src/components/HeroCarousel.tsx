import { ChevronLeft, ChevronRight } from 'lucide-react';
import { useState, useEffect, useCallback } from 'react';

type HeroSlide = {
  id: number;
  label: string;
  title: string;
  subtitle: string;
  imageUrl: string;
};

const heroSlides: HeroSlide[] = [
  {
    id: 1,
    label: 'CURATED COLLECTION',
    title: 'Promo Tees',
    subtitle: '가장 좋아하는 영화를 입어보세요',
    imageUrl: 'https://images.unsplash.com/photo-1523381210434-271e8be1f52b?w=1600&h=600&fit=crop&q=80',
  },
  {
    id: 2,
    label: 'NEW ARRIVALS',
    title: 'Spring Collection',
    subtitle: '봄을 위한 새로운 스타일',
    imageUrl: 'https://images.unsplash.com/photo-1441984904996-e0b6ba687e04?w=1600&h=600&fit=crop&q=80',
  },
  {
    id: 3,
    label: 'TRENDING NOW',
    title: 'Street Style',
    subtitle: '스트릿 패션의 새로운 트렌드',
    imageUrl: 'https://images.unsplash.com/photo-1445205170230-053b83016050?w=1600&h=600&fit=crop&q=80',
  },
];

export function HeroCarousel() {
  const [currentSlide, setCurrentSlide] = useState(0);
  const [isAutoPlaying, setIsAutoPlaying] = useState(true);

  const nextSlide = useCallback(() => {
    setCurrentSlide((prev) => (prev + 1) % heroSlides.length);
  }, []);

  const prevSlide = useCallback(() => {
    setCurrentSlide((prev) => (prev - 1 + heroSlides.length) % heroSlides.length);
  }, []);

  const goToSlide = (index: number) => {
    setCurrentSlide(index);
    setIsAutoPlaying(false);
    setTimeout(() => setIsAutoPlaying(true), 5000);
  };

  useEffect(() => {
    if (!isAutoPlaying) return;
    const interval = setInterval(nextSlide, 5000);
    return () => clearInterval(interval);
  }, [isAutoPlaying, nextSlide]);

  const slide = heroSlides[currentSlide];

  return (
    <section className="relative w-full h-[400px] md:h-[500px] lg:h-[600px] overflow-hidden bg-foreground">
      {/* Background Image */}
      <div className="absolute inset-0">
        <img
          src={slide.imageUrl}
          alt={slide.title}
          className="w-full h-full object-cover transition-transform duration-700"
        />
        <div className="absolute inset-0 bg-gradient-to-r from-black/70 via-black/40 to-transparent" />
      </div>

      {/* Content */}
      <div className="relative z-10 flex flex-col justify-end h-full max-w-[1400px] mx-auto px-4 lg:px-8 pb-12 md:pb-16">
        <span className="text-accent text-xs font-bold tracking-widest mb-2">
          {slide.label}
        </span>
        <h2 className="text-4xl md:text-5xl lg:text-6xl font-black text-primary-foreground mb-3 leading-tight">
          {slide.title}
        </h2>
        <p className="text-primary-foreground/80 text-base md:text-lg font-medium max-w-md">
          {slide.subtitle}
        </p>

        {/* Slide Indicators */}
        <div className="flex items-center gap-2 mt-8">
          {heroSlides.map((_, index) => (
            <button
              key={index}
              onClick={() => goToSlide(index)}
              className={`transition-all duration-300 ${
                index === currentSlide
                  ? 'w-8 h-2 bg-primary-foreground rounded-full'
                  : 'w-2 h-2 bg-primary-foreground/40 rounded-full hover:bg-primary-foreground/60'
              }`}
              aria-label={`Go to slide ${index + 1}`}
            />
          ))}
        </div>
      </div>

      {/* Navigation Arrows */}
      <button
        onClick={() => {
          prevSlide();
          setIsAutoPlaying(false);
          setTimeout(() => setIsAutoPlaying(true), 5000);
        }}
        className="absolute left-4 top-1/2 -translate-y-1/2 w-10 h-10 md:w-12 md:h-12 flex items-center justify-center bg-primary-foreground/10 hover:bg-primary-foreground/20 backdrop-blur-sm rounded-full text-primary-foreground transition-colors"
        aria-label="Previous slide"
      >
        <ChevronLeft className="w-5 h-5 md:w-6 md:h-6" />
      </button>
      <button
        onClick={() => {
          nextSlide();
          setIsAutoPlaying(false);
          setTimeout(() => setIsAutoPlaying(true), 5000);
        }}
        className="absolute right-4 top-1/2 -translate-y-1/2 w-10 h-10 md:w-12 md:h-12 flex items-center justify-center bg-primary-foreground/10 hover:bg-primary-foreground/20 backdrop-blur-sm rounded-full text-primary-foreground transition-colors"
        aria-label="Next slide"
      >
        <ChevronRight className="w-5 h-5 md:w-6 md:h-6" />
      </button>
    </section>
  );
}
