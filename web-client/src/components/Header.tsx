import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="bg-background/80 backdrop-blur-sm border-b border-border py-4 sticky top-0 z-50">
      <div className="container mx-auto px-4">
        <div className="flex items-center justify-between gap-10">
          <div className="flex-shrink-0">
            <img
              src="/logo.svg"
              alt="NicheExplorer Logo"
              className="h-10 w-auto transition-transform duration-300"
            />
          </div>
          <nav className="flex items-center gap-6 text-sm font-medium">
            {/* Add navigation items here if needed */}
          </nav>
        </div>
      </div>
    </header>
  );
};

export default Header;
