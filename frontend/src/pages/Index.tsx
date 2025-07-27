import React, { useState } from 'react';
import { Music, AlertCircle } from 'lucide-react';
import { SearchBar } from '@/components/SearchBar';
import { SearchResults } from '@/components/SearchResults';
import { AudioPlayer } from '@/components/AudioPlayer';
import { useToast } from '@/hooks/use-toast';
import { getApiUrl } from '@/config/api';

interface SearchResult {
  title: string;
  youtubeUrl: string;
  thumbnailUrl: string;
}

interface CurrentTrack {
  title: string;
  url: string;
}

const Index = () => {
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [currentTrack, setCurrentTrack] = useState<CurrentTrack | null>(null);
  const [currentTrackIndex, setCurrentTrackIndex] = useState<number>(-1);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoadingAudio, setIsLoadingAudio] = useState(false);
  const { toast } = useToast();

  // Search for YouTube videos
  const handleSearch = async (query: string) => {
    setIsSearching(true);
    try {
      const formData = new FormData();
      formData.append('searchQuery', query);

      const response = await fetch(getApiUrl('search'), {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }

      const results = await response.json();
      setSearchResults(results);
      
      if (results.length === 0) {
        toast({
          title: "No results found",
          description: "Try searching with different keywords.",
        });
      }
    } catch (error) {
      console.error('Search error:', error);
      toast({
        title: "Search failed",
        description: "Unable to search YouTube. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSearching(false);
    }
  };

  // Play a selected track
  const handlePlay = async (result: SearchResult) => {
    setIsLoadingAudio(true);
    try {
      const formData = new FormData();
      formData.append('youtubeUrl', result.youtubeUrl);

      const response = await fetch(getApiUrl('download'), {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Download failed: ${response.status}`);
      }

      // Get the title from response headers
      const videoTitle = result.title;
      
      // Create blob URL for audio
      const audioBlob = await response.blob();
      const audioUrl = URL.createObjectURL(audioBlob);
      
      // Find the index of the current track in search results
      const trackIndex = searchResults.findIndex(r => r.youtubeUrl === result.youtubeUrl);
      
      setCurrentTrack({
        title: videoTitle,
        url: audioUrl,
      });
      setCurrentTrackIndex(trackIndex);

      toast({
        title: "Now playing",
        description: videoTitle,
      });
    } catch (error) {
      console.error('Play error:', error);
      toast({
        title: "Playback failed",
        description: "Unable to load audio. Please try another track.",
        variant: "destructive",
      });
    } finally {
      setIsLoadingAudio(false);
    }
  };

  // Navigate to next track
  const handleNext = () => {
    if (currentTrackIndex < searchResults.length - 1) {
      const nextResult = searchResults[currentTrackIndex + 1];
      handlePlay(nextResult);
    }
  };

  // Navigate to previous track
  const handlePrevious = () => {
    if (currentTrackIndex > 0) {
      const previousResult = searchResults[currentTrackIndex - 1];
      handlePlay(previousResult);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-hero">
      {/* Header */}
      <header className="bg-background/80 backdrop-blur-md border-b border-border sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-primary rounded-lg flex items-center justify-center">
              <Music className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">Music Player</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8 pb-32">
        {/* Search Section */}
        <div className="text-center mb-8">
          <h2 className="text-4xl font-bold text-foreground mb-4">
            Discover Your Music
          </h2>
          <p className="text-muted-foreground text-lg max-w-2xl mx-auto mb-8">
            Search and stream music from YouTube with our beautiful player interface.
          </p>
          
          <SearchBar onSearch={handleSearch} isLoading={isSearching} />
        </div>

        {/* Error State */}
        {!navigator.onLine && (
          <div className="flex items-center justify-center gap-2 text-muted-foreground mb-6">
            <AlertCircle className="w-5 h-5" />
            <span>You appear to be offline. Some features may not work.</span>
          </div>
        )}

        {/* Search Results */}
        <SearchResults
          results={searchResults}
          onPlay={handlePlay}
          currentPlaying={currentTrack ? searchResults[currentTrackIndex]?.youtubeUrl : undefined}
          isLoading={isLoadingAudio}
        />
      </main>

      {/* Audio Player */}
      <AudioPlayer
        currentTrack={currentTrack}
        onNext={handleNext}
        onPrevious={handlePrevious}
        hasNext={currentTrackIndex < searchResults.length - 1}
        hasPrevious={currentTrackIndex > 0}
      />
    </div>
  );
};

export default Index;