import { Flex, Stack, Tooltip, UnstyledButton, rem, useMantineTheme } from '@mantine/core';
import type { NavigationItem } from '../data/navigation';

interface SidebarSection {
  id: string;
  items: NavigationItem[];
}

interface SidebarProps {
  sections: SidebarSection[];
  activeId: string;
  onSelect: (id: string) => void;
}

const SidebarButton = ({
  item,
  isActive,
  onSelect
}: {
  item: NavigationItem;
  isActive: boolean;
  onSelect: (id: string) => void;
}) => {
  const theme = useMantineTheme();
  const { icon: IconComponent, label } = item;
  const inactiveColor = theme.colors.gray[6];
  const activeColor = theme.colors.teal[6];
  const activeBackground = theme.colors.teal[0];
  const borderColor = theme.colors.teal[3];

  return (
    <Tooltip label={label} position="right" offset={8}>
      <UnstyledButton
        aria-label={label}
        data-active={isActive || undefined}
        onClick={() => onSelect(item.id)}
        style={{
          width: rem(46),
          height: rem(46),
          borderRadius: theme.radius.xl,
          display: 'grid',
          placeItems: 'center',
          color: isActive ? activeColor : inactiveColor,
          backgroundColor: isActive ? activeBackground : 'transparent',
          border: isActive ? `${rem(1)} solid ${borderColor}` : `${rem(1)} solid transparent`,
          transition: 'background-color 120ms ease, color 120ms ease',
          cursor: 'pointer',
          padding: theme.spacing.xs
        }}
      >
        <IconComponent size={22} stroke={1.5} />
      </UnstyledButton>
    </Tooltip>
  );
};

export const Sidebar = ({ sections, activeId, onSelect }: SidebarProps) => {
  const theme = useMantineTheme();

  const sidebarBackground = theme.colors.gray[0];
  const borderColor = theme.colors.gray[2];

  const topItems = sections.length > 1 ? sections.slice(0, -1) : sections;
  const bottomItems = sections.length > 1 ? sections.slice(-1) : [];

  return (
    <Flex
      component="nav"
      direction="column"
      justify="space-between"
      align="center"
      h="100%"
      w={rem(84)}
      px="md"
      py="lg"
      bg={sidebarBackground}
      style={{
        borderRight: `${rem(1)} solid ${borderColor}`,
        flexShrink: 0
      }}
    >
      <Stack gap="lg">
        {topItems.flatMap((section) =>
          section.items.map((item) => (
            <SidebarButton
              key={item.id}
              item={item}
              isActive={item.id === activeId}
              onSelect={onSelect}
            />
          ))
        )}
      </Stack>

      <Stack gap="lg">
        {bottomItems.flatMap((section) =>
          section.items.map((item) => (
            <SidebarButton
              key={item.id}
              item={item}
              isActive={item.id === activeId}
              onSelect={onSelect}
            />
          ))
        )}
      </Stack>
    </Flex>
  );
};
