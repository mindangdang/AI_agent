import { Search, ChevronDown, Menu, X } from 'lucide-react';
import { useState } from 'react';
import type { AppUser } from '../types/user';

type HeaderProps = {
  user: AppUser | null;
  onLogout: () => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  onSearchSubmit: () => void;
  currentTab: string;
  onTabChange: (tab: 'feed' | 'search' | 'profile') => void;
};

const categories = [
  { id: 'search', label: '검색', hasDropdown: false },
  { id: 'feed', label: '피드', hasDropdown: false },
  { id: 'profile', label: '테이스팅', hasDropdown: false },
];

export function Header({
  user,
  onLogout,
  searchQuery,
  onSearchChange,
  onSearchSubmit,
  currentTab,
  onTabChange,
}: HeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const handleSearchKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      onSearchSubmit();
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-background border-b border-border">
      {/* Main Header */}
      <div className="flex items-center justify-between h-16 px-4 lg:px-8 max-w-[1400px] mx-auto">
        {/* Logo */}
        <a href="/" className="flex items-center gap-2 shrink-0">
          <span className="text-2xl font-black tracking-tight text-foreground">POSE</span>
        </a>

        {/* Search Bar - Desktop */}
        <div className="hidden md:flex flex-1 max-w-xl mx-8">
          <div className="relative w-full">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              placeholder="상품, 브랜드 및 유저 검색"
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              onKeyDown={handleSearchKeyDown}
              className="w-full h-11 pl-12 pr-4 bg-muted rounded-full text-sm font-medium placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-foreground/10"
            />
          </div>
        </div>

        {/* Right Navigation - Desktop */}
        <nav className="hidden md:flex items-center gap-6">
          {user ? (
            <>
              <span className="text-sm font-medium text-foreground">
                @{user.name || user.username || 'user'}
              </span>
              <button
                onClick={onLogout}
                className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
              >
                로그아웃
              </button>
            </>
          ) : (
            <>
              <button className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                회원 가입
              </button>
              <button className="text-sm font-medium text-muted-foreground hover:text-foreground transition-colors">
                로그인
              </button>
            </>
          )}
        </nav>

        {/* Mobile Menu Button */}
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="md:hidden p-2 text-foreground"
          aria-label="Toggle menu"
        >
          {isMobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </div>

      {/* Category Navigation - Desktop */}
      <div className="hidden md:block border-t border-border">
        <nav className="category-nav flex items-center gap-6 h-12 px-4 lg:px-8 max-w-[1400px] mx-auto overflow-x-auto">
          {categories.map((category) => (
            <button
              key={category.id}
              onClick={() => onTabChange(category.id as 'feed' | 'search' | 'profile')}
              className={`flex items-center gap-1 text-sm font-medium whitespace-nowrap transition-colors ${
                currentTab === category.id
                  ? 'text-foreground'
                  : 'text-muted-foreground hover:text-foreground'
              }`}
            >
              {category.label}
              {category.hasDropdown && <ChevronDown className="w-4 h-4" />}
            </button>
          ))}
        </nav>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 bg-background border-b border-border shadow-lg">
          {/* Mobile Search */}
          <div className="p-4">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <input
                type="text"
                placeholder="상품, 브랜드 및 유저 검색"
                value={searchQuery}
                onChange={(e) => onSearchChange(e.target.value)}
                onKeyDown={handleSearchKeyDown}
                className="w-full h-11 pl-12 pr-4 bg-muted rounded-full text-sm font-medium placeholder:text-muted-foreground focus:outline-none"
              />
            </div>
          </div>

          {/* Mobile Categories */}
          <nav className="border-t border-border">
            {categories.map((category) => (
              <button
                key={category.id}
                onClick={() => {
                  onTabChange(category.id as 'feed' | 'search' | 'profile');
                  setIsMobileMenuOpen(false);
                }}
                className={`w-full flex items-center justify-between px-4 py-3 text-sm font-medium ${
                  currentTab === category.id
                    ? 'text-foreground bg-muted'
                    : 'text-muted-foreground'
                }`}
              >
                {category.label}
                {category.hasDropdown && <ChevronDown className="w-4 h-4" />}
              </button>
            ))}
          </nav>

          {/* Mobile User Actions */}
          <div className="border-t border-border p-4 space-y-2">
            {user ? (
              <>
                <div className="text-sm font-medium text-foreground py-2">
                  @{user.name || user.username || 'user'}
                </div>
                <button
                  onClick={() => {
                    onLogout();
                    setIsMobileMenuOpen(false);
                  }}
                  className="w-full text-left text-sm font-medium text-muted-foreground py-2"
                >
                  로그아웃
                </button>
              </>
            ) : (
              <>
                <button className="w-full text-left text-sm font-medium text-muted-foreground py-2">
                  회원 가입
                </button>
                <button className="w-full text-left text-sm font-medium text-muted-foreground py-2">
                  로그인
                </button>
              </>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
