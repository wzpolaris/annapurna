import {
  IconCirclePlus,
  IconClock,
  IconHome,
  IconLayoutGrid,
  IconMessage,
  IconSettings,
  IconSparkles,
  IconUser
} from '@tabler/icons-react';

type TablerIconComponent = typeof IconCirclePlus;

export interface NavigationItem {
  id: string;
  label: string;
  icon: TablerIconComponent;
  isActive?: boolean;
}

export const primaryNavigation: NavigationItem[] = [
  {
    id: 'new-chat',
    label: 'New chat',
    icon: IconCirclePlus
  },
  {
    id: 'home',
    label: 'Home',
    icon: IconHome,
    isActive: true
  },
  {
    id: 'discover',
    label: 'Discover',
    icon: IconSparkles
  },
  {
    id: 'spaces',
    label: 'Spaces',
    icon: IconLayoutGrid
  }
];

export const secondaryNavigation: NavigationItem[] = [
  {
    id: 'messages',
    label: 'Messages',
    icon: IconMessage
  },
  {
    id: 'recent',
    label: 'Recent',
    icon: IconClock
  },
  {
    id: 'account',
    label: 'Account',
    icon: IconUser
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: IconSettings
  }
];
