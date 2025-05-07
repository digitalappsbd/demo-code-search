import { useState } from "react";
import {
  Group,
  Box,
  Collapse,
  ThemeIcon,
  UnstyledButton,
  rem,
  Badge,
} from "@mantine/core";
import { IconChevronRight } from "@tabler/icons-react";
import classes from "./FileGroup.module.css";

interface LinksGroupProps {
  label: string;
  icon: any;
  initiallyOpened?: boolean;
  id?: string;
  links?: LinksGroupProps[];
  match_type?: string;
  matched_field?: string;
}

// Function to get a more user-friendly display name for matched field
const getMatchedFieldDisplayName = (field?: string) => {
  if (!field) return "";
  
  switch (field) {
    case "file_name":
      return "Filename";
    case "function_name":
      return "Function";
    case "file_path":
      return "Path";
    case "content":
      return "Content";
    case "code":
      return "Code";
    case "docstring":
      return "Docstring";
    default:
      return field;
  }
};

export function LinksGroup({
  icon: Icon,
  label,
  initiallyOpened,
  links,
  match_type,
  matched_field,
}: LinksGroupProps) {
  const [opened, setOpened] = useState(initiallyOpened || false);

  const getFileRoute = () => {
    if (links?.length === 1 && links[0].links) {
      label = `${label}/${links[0].label}`;
      links = links[0].links;
      getFileRoute();
    }
  };

  getFileRoute();

  const items = links?.map((link) => {
    if (link.links) {
      return (
        <Box key={link.label} ml="sm" className={classes.lind}>
          <LinksGroup {...link} />
        </Box>
      );
    } else {
      return (
        <UnstyledButton
          key={link.label}
          className={classes.control}
          variant="transparent"
        >
          <Box
            style={{ display: "flex", alignItems: "center" }}
            ml={"sm"}
            className={classes.lind}
            onClick={() => {
              // First try to find the element by ID (for navigation)
              const element = document.getElementById(link.id ?? link.label);

              if (element) {
                element.scrollIntoView({ behavior: "smooth"});
              }
            }}
          >
            <ThemeIcon variant="transparent" size={30}>
              <link.icon style={{ width: rem(18), height: rem(18) }} />
            </ThemeIcon>
            <Box mr="xs">{link.label}</Box>
            {link.match_type && (
              <Group gap="xs">
                <Badge 
                  size="xs"
                  color={link.match_type === "text" ? "blue" : 
                         link.match_type === "hybrid" ? "grape" : "green"} 
                  variant="light"
                >
                  {link.match_type.charAt(0).toUpperCase() + link.match_type.slice(1)}
                </Badge>
                {link.matched_field && (
                  <Badge size="xs" color="cyan" variant="outline">
                    {getMatchedFieldDisplayName(link.matched_field)}
                  </Badge>
                )}
              </Group>
            )}
          </Box>
        </UnstyledButton>
      );
    }
  });

  return (
    <>
      <UnstyledButton
        onClick={() => setOpened((o) => !o)}
        className={classes.control}
      >
        <Group justify="space-between" gap={0} wrap="nowrap">
          <Box style={{ display: "flex", alignItems: "center" }}>
            <ThemeIcon variant="transparent" size={30}>
              <Icon style={{ width: rem(18), height: rem(18) }} />
            </ThemeIcon>
            <Box>{label}</Box>
            {match_type && (
              <Group ml="xs" gap="xs">
                <Badge 
                  size="xs"
                  color={match_type === "text" ? "blue" : 
                         match_type === "hybrid" ? "grape" : "green"} 
                  variant="light"
                >
                  {match_type.charAt(0).toUpperCase() + match_type.slice(1)}
                </Badge>
                {matched_field && (
                  <Badge size="xs" color="cyan" variant="outline">
                    {getMatchedFieldDisplayName(matched_field)}
                  </Badge>
                )}
              </Group>
            )}
          </Box>
          {links?.length && (
            <IconChevronRight
              className={classes.chevron}
              stroke={1.5}
              style={{
                width: rem(16),
                height: rem(16),
                transform: opened ? "rotate(-90deg)" : "none",
              }}
            />
          )}
        </Group>
      </UnstyledButton>
      {links?.length ? <Collapse in={opened}>{items}</Collapse> : null}
    </>
  );
}
