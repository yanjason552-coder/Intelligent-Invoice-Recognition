import React from 'react';
import { Box, Button, Heading, Text, VStack } from '@chakra-ui/react';

const InventoryEdit: React.FC = () => {
  const handleSave = () => {
    console.log('保存库存明细');
  };

  return (
    <Box p={6}>
      <VStack gap={4} align="start">
        <Heading size="lg">库存明细编辑</Heading>
        <Text>这是库存明细编辑页面</Text>
        <Button colorScheme="blue" onClick={handleSave}>
          保存
        </Button>
      </VStack>
    </Box>
  );
};

export default InventoryEdit; 