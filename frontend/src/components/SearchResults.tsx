import React from 'react';
import { Play, Music } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import placeholderImage from '@/assets/music-placeholder.jpg';

interface SearchResult {
  title: string;
  youtubeUrl: string;
  thumbnailUrl: string;
}

interface SearchResultsProps {
  results: SearchResult[];
  onPlay: (result: SearchResult) => void;
  currentPlaying?: string;
  isLoading?: boolean;
}

export const SearchResults: React.FC<SearchResultsProps> = ({
  results,
  onPlay,
  currentPlaying,
  isLoading
}) => {
  if (results.length === 0) {
    return (
      <div className="text-center py-12">
        <Music className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
        <p className="text-muted-foreground text-lg">
          No results yet. Search for your favorite music!
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 mb-8">
      {results.map((result, index) => (
        <Card 
          key={index} 
          className="bg-result-card hover:bg-result-card-hover transition-all duration-300 hover:shadow-card group cursor-pointer border-border"
          onClick={() => onPlay(result)}
        >
          <CardContent className="p-4">
            <div className="relative mb-3">
              <img
                src={result.thumbnailUrl || placeholderImage}
                alt={result.title}
                className="w-full aspect-video object-cover rounded-md"
                onError={(e) => {
                  (e.target as HTMLImageElement).src = placeholderImage;
                }}
              />
              <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-md flex items-center justify-center">
                <Button
                  size="sm"
                  className="bg-primary hover:bg-primary/90 text-primary-foreground shadow-glow"
                  disabled={isLoading}
                >
                  <Play className="w-4 h-4 mr-1" />
                  Play
                </Button>
              </div>
              {currentPlaying === result.youtubeUrl && (
                <div className="absolute top-2 right-2 w-3 h-3 bg-primary rounded-full animate-pulse"></div>
              )}
            </div>
            <h3 className="text-sm font-medium text-foreground line-clamp-2 group-hover:text-primary transition-colors duration-300">
              {result.title}
            </h3>
          </CardContent>
        </Card>
      ))}
    </div>
  );
};