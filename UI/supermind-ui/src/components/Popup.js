import React, { useState, useEffect } from 'react';
import './Popup.css';

export default function Popup({ cardData, onClose, isDarkTheme }) {
  // State variables
  const [notes, setNotes] = useState('');
  const [tags, setTags] = useState(
    cardData?.Tags ? 
    cardData.Tags.split(',').map(tag => tag.trim()) : 
    []
  );
  const [iframeError, setIframeError] = useState(false);
  const [showFullTitle, setShowFullTitle] = useState(false);
  const [imageUrl, setImageUrl] = useState(cardData?.["Thumbnail URL"]);
  const [showFullSummary, setShowFullSummary] = useState(false);
  const [showFullTags, setShowFullTags] = useState(false);

  // Handle "Escape" key to close popup and disable background scrolling
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = 'auto';
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [onClose]);

  // Fetch Instagram thumbnail using proxy
  useEffect(() => {
    if (!cardData?.["Thumbnail URL"] || cardData["Thumbnail URL"].startsWith("/assets/")) return;
    if (cardData?.url?.includes('instagram.com')) {
      const proxyUrl = `https://proxy.corsfix.com/?${cardData["Thumbnail URL"]}`;
      fetch(proxyUrl)
        .then(response => response.blob())
        .then(imageBlob => setImageUrl(URL.createObjectURL(imageBlob)))
        .catch(() => setImageUrl("/assets/image-placeholder.png"));
    }
  }, [cardData]);

  // Handle adding new tags
  const handleTagAdd = (e) => {
    if (e.key === 'Enter' && e.target.value.trim()) {
      setTags([...tags, e.target.value.trim()]);
      e.target.value = '';
    }
  };

  // Truncate text to a specified limit
  const truncateText = (text, limit) => {
    if (text?.length <= limit) return text;
    return text?.substring(0, limit) + '...';
  };

  // Add helper function to check text selection
  const hasSelectedText = () => {
    return window.getSelection().toString().length > 0;
  };

  // Render content based on URL type
  const renderContent = () => {
    if (cardData?.url?.includes('instagram.com')) {
      return (
        <div className="fallback-content instagram-content">
          <div className="instagram-thumbnail-wrapper">
            <img 
              src={imageUrl || "/assets/image-placeholder.png"}
              alt={cardData.Title}
              className="instagram-image"
            />
          </div>
        </div>
      );
    }
    if (cardData?.url?.includes('youtube')) {
      return (
        <iframe
          src={`https://www.youtube.com/embed/${extractYouTubeId(cardData.url)}`}
          width="1280"
          height="720"
          frameBorder="0"
          allowFullScreen
          title="YouTube Video"
        />
      );
    }
    if (!iframeError) {
      return (
        <iframe
          src={cardData.url}
          width="1280"
          height="720"
          title="Preview"
          sandbox="allow-same-origin allow-scripts"
          onError={() => setIframeError(true)}
        />
      );
    }
    return (
      <div className="fallback-content">
        <img 
          src={imageUrl || "/assets/image-placeholder.png"}
          alt={cardData.Title}
          className="fallback-image"
        />
        <a 
          href={cardData.url} 
          target="_blank" 
          rel="noopener noreferrer"
          className="visit-button"
        >
          Visit Original
        </a>
      </div>
    );
  };

  return (
    <div className={`popup-overlay ${isDarkTheme ? 'dark-theme' : 'light-theme'}`} onClick={onClose}>
      <div className={`popup-content ${isDarkTheme ? 'dark-theme' : 'light-theme'}`} onClick={(e) => e.stopPropagation()}>
        <div className="popup-left">
          {renderContent()}
          <a
            href={cardData.url}
            target="_blank"
            rel="noopener noreferrer"
            className="visit-button"
          >
            Visit Original
          </a>
        </div>
        <div className="popup-right">
          <h2 
            className="truncated-title" 
            onClick={(e) => {
              if (!hasSelectedText()) {
                setShowFullTitle(!showFullTitle);
              }
            }}
            title={cardData.Title}
          >
            {showFullTitle ? cardData.Title : truncateText(cardData.Title, 100)}
          </h2>
          <div className="section-label">Summary:</div>
          <p 
            className="summary-text"
            onClick={(e) => {
              if (!hasSelectedText()) {
                setShowFullSummary(!showFullSummary);
              }
            }}
          >
            {showFullSummary ? cardData.Summary : truncateText(cardData.Summary, 700)}
          </p>
          <div className="section-label">Tags:</div>
          <div
            className="tags"
            onClick={(e) => {
              if (!hasSelectedText()) {
                setShowFullTags(!showFullTags);
              }
            }}
          >
            {showFullTags ? tags.map((tag, index) => (
              <span key={index} className="tag">{tag}</span>
            )) : tags.slice(0, 15).map((tag, index) => (
              <span key={index} className="tag">{tag}</span>
            ))}
            <input
              type="text"
              placeholder="Add a tag..."
              onKeyPress={handleTagAdd}
            />
          </div>
          <textarea
            placeholder="Add your notes here..."
            value={notes}
            onChange={(e) => setNotes(e.target.value)}
            style={{ color: isDarkTheme ? 'white' : 'black' }}
          />
          <div className="popup-buttons">
            <button style={{ backgroundImage: 'url("/assets/delete.png")', backgroundSize: '20px 20px', backgroundRepeat: 'no-repeat', backgroundPosition: 'center' }}/>
            <button style={{ backgroundImage: 'url("/assets/share.png")', backgroundSize: '20px 20px', backgroundRepeat: 'no-repeat', backgroundPosition: 'center' }}/>
            <button style={{ backgroundImage: 'url("/assets/save.png")', backgroundSize: '20px 20px', backgroundRepeat: 'no-repeat', backgroundPosition: 'center' }}/>
          </div>
        </div>
      </div>
    </div>
  );
}

// Extract YouTube video ID from URL
function extractYouTubeId(url) {
  const regExp = /(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|embed\/))([\w-]{11})/;
  const match = url?.match(regExp);
  return match ? match[1] : null;
}