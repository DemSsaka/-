export type Currency = "USD" | "EUR" | "GBP" | "RUB";

export type Item = {
  id: number;
  name: string;
  url?: string | null;
  image_url?: string | null;
  price_cents: number;
  allow_contributions: boolean;
  notes?: string | null;
  position: number;
  is_archived: boolean;
  reserved: boolean;
  reserved_by_me: boolean;
  reserved_at?: string | null;
  collected_cents: number;
  my_contribution_cents?: number | null;
  created_at: string;
  updated_at: string;
};

export type Wishlist = {
  id: number;
  public_id: string;
  title: string;
  description?: string | null;
  currency: Currency;
  is_public: boolean;
  is_owner: boolean;
  created_at: string;
  updated_at: string;
  items: Item[];
};

export type WishlistSummary = {
  id: number;
  public_id: string;
  title: string;
  currency: Currency;
  is_public: boolean;
  item_count: number;
  created_at: string;
};

export type PublicWishlistSummary = {
  public_id: string;
  title: string;
  author_name: string;
  currency: Currency;
  item_count: number;
  updated_at: string;
};

export type UserProfile = {
  id: number;
  email: string;
  nickname?: string | null;
  avatar_url?: string | null;
  bio?: string | null;
  birth_date?: string | null;
  theme: "light" | "dark";
  balance_cents: number;
  email_verified: boolean;
};

export type NotificationItem = {
  id: number;
  type: string;
  title: string;
  body?: string | null;
  created_at: string;
  read_at?: string | null;
};
