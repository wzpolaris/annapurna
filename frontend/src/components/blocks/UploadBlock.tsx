import { useMemo, useRef, useState } from 'react';
import { Box, Button, Group, Stack, Text, Textarea } from '@mantine/core';

import Pdf2pViewerBlock from './pdf2p/Pdf2pViewerBlock';

interface UploadBlockProps {
  content: string;
}

interface UploadBlockConfig {
  title: string;
  placeholder: string;
}

const DEFAULT_CONFIG: UploadBlockConfig = {
  title: 'Upload a file or paste data in the text area below',
  placeholder: 'Paste CSV or text data here'
};

const formatSize = (byteSize: number) => {
  if (Number.isNaN(byteSize)) {
    return '';
  }
  if (byteSize >= 1024 * 1024) {
    return `${(byteSize / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (byteSize >= 1024) {
    return `${(byteSize / 1024).toFixed(1)} KB`;
  }
  return `${byteSize} B`;
};

export const UploadBlock = ({ content }: UploadBlockProps) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [textValue, setTextValue] = useState('');
  const [selectedFileName, setSelectedFileName] = useState('');
  const [selectedFileSize, setSelectedFileSize] = useState('');
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const config = useMemo<UploadBlockConfig>(() => {
    if (!content) {
      return DEFAULT_CONFIG;
    }
    try {
      const parsed = JSON.parse(content) as Partial<UploadBlockConfig>;
      return {
        title: parsed.title ?? DEFAULT_CONFIG.title,
        placeholder: parsed.placeholder ?? DEFAULT_CONFIG.placeholder
      };
    } catch {
      return DEFAULT_CONFIG;
    }
  }, [content]);

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const resetStates = () => {
    setPdfUrl(null);
    setTextValue('');
  };

  const handleFileChange: React.ChangeEventHandler<HTMLInputElement> = (event) => {
    const { files } = event.target;
    const file = files?.[0];
    if (!file) {
      setSelectedFileName('');
      setSelectedFileSize('');
      setErrorMessage(null);
      resetStates();
      event.target.value = '';
      return;
    }

    setSelectedFileName(file.name);
    setSelectedFileSize(formatSize(file.size));
    setErrorMessage(null);

    const reader = new FileReader();

    reader.onerror = () => {
      setErrorMessage('Unable to read file.');
      resetStates();
    };

    if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
      reader.onload = () => {
        const result = reader.result;
        if (typeof result === 'string') {
          setPdfUrl(result);
          setTextValue('');
        } else {
          setErrorMessage('Unable to read PDF contents.');
          resetStates();
        }
      };
      reader.readAsDataURL(file);
      return;
    }

    reader.onload = () => {
      if (typeof reader.result === 'string') {
        setTextValue(reader.result);
        setPdfUrl(null);
      } else {
        setErrorMessage('Unable to read text contents.');
        resetStates();
      }
    };
    reader.readAsText(file);
    event.target.value = '';
  };

  return (
    <Stack gap="md">
      <Group justify="space-between" align="flex-start" wrap="wrap" gap="sm">
        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Text fw={600}>{config.title}</Text>
          {selectedFileName ? (
            <Text size="xs" c="dimmed" truncate>
              {selectedFileSize ? `${selectedFileName} (${selectedFileSize})` : selectedFileName}
            </Text>
          ) : null}
        </Stack>
        <Button
          size="xs"
          variant="light"
          color="teal"
          onClick={handleBrowseClick}
        >
          Upload file
        </Button>
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.txt,.pdf,text/csv,text/plain,application/pdf"
          style={{ display: 'none' }}
          onChange={handleFileChange}
        />
      </Group>

      <Textarea
        value={textValue}
        onChange={(event) => setTextValue(event.currentTarget.value)}
        minRows={8}
        placeholder={config.placeholder}
        autosize={false}
        styles={{
          input: {
            resize: 'none'
          }
        }}
      />

      {errorMessage ? (
        <Text size="xs" c="red">
          {errorMessage}
        </Text>
      ) : null}

      {pdfUrl ? (
        <Box>
          <Pdf2pViewerBlock
            fileUrl={pdfUrl}
            filename={selectedFileName || undefined}
            fileSize={selectedFileSize || undefined}
          />
        </Box>
      ) : null}
    </Stack>
  );
};
