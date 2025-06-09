import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/router';
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardFooter, 
  CardHeader, 
  CardTitle 
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { AlertCircle, CheckCircle, Clock, FileText } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import { useAuth } from '@/hooks/useAuth';
import DashboardLayout from '@/components/layouts/DashboardLayout';

// Types
interface PromptVersion {
  version: string;
  status: string;
  created_at: string;
  created_by?: string;
  description?: string;
}

const PromptsPage = () => {
  const router = useRouter();
  const { user } = useAuth();
  const [promptVersions, setPromptVersions] = useState<PromptVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchPromptVersions = async () => {
      try {
        const response = await fetch('/api/dashboard/prompts/versions');
        if (!response.ok) {
          throw new Error('Failed to fetch prompt versions');
        }
        const data = await response.json();
        setPromptVersions(data);
      } catch (err) {
        setError('Error loading prompt versions');
        console.error(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPromptVersions();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-500"><CheckCircle className="w-3 h-3 mr-1" /> Active</Badge>;
      case 'candidate':
        return <Badge className="bg-yellow-500"><Clock className="w-3 h-3 mr-1" /> Pending</Badge>;
      case 'rejected':
        return <Badge className="bg-red-500"><AlertCircle className="w-3 h-3 mr-1" /> Rejected</Badge>;
      default:
        return <Badge className="bg-gray-500">{status}</Badge>;
    }
  };

  const handleViewPrompt = (version: string) => {
    router.push(`/prompts/${version}`);
  };

  const handleViewDiff = (version: string) => {
    router.push(`/prompts/diff/${version}`);
  };

  const renderPromptCard = (prompt: PromptVersion) => (
    <Card key={prompt.version} className="mb-4">
      <CardHeader>
        <div className="flex justify-between items-center">
          <CardTitle>Version {prompt.version}</CardTitle>
          {getStatusBadge(prompt.status)}
        </div>
        <CardDescription>
          Created {formatDistanceToNow(new Date(prompt.created_at))} ago
          {prompt.created_by && ` by ${prompt.created_by}`}
        </CardDescription>
      </CardHeader>
      <CardContent>
        {prompt.description || 'No description provided'}
      </CardContent>
      <CardFooter className="flex justify-end gap-2">
        <Button variant="outline" onClick={() => handleViewPrompt(prompt.version)}>
          <FileText className="w-4 h-4 mr-2" /> View
        </Button>
        {prompt.status === 'candidate' && (
          <Button variant="default" onClick={() => handleViewDiff(prompt.version)}>
            Compare Changes
          </Button>
        )}
      </CardFooter>
    </Card>
  );

  if (loading) {
    return <DashboardLayout>Loading prompt versions...</DashboardLayout>;
  }

  if (error) {
    return <DashboardLayout>{error}</DashboardLayout>;
  }

  const activePrompts = promptVersions.filter(p => p.status === 'active');
  const candidatePrompts = promptVersions.filter(p => p.status === 'candidate');
  const rejectedPrompts = promptVersions.filter(p => p.status === 'rejected');

  return (
    <DashboardLayout>
      <div className="container mx-auto py-6">
        <h1 className="text-3xl font-bold mb-6">Prompt Management</h1>
        
        <Tabs defaultValue="active">
          <TabsList className="mb-4">
            <TabsTrigger value="active">
              Active ({activePrompts.length})
            </TabsTrigger>
            <TabsTrigger value="candidates">
              Pending Review ({candidatePrompts.length})
            </TabsTrigger>
            <TabsTrigger value="history">
              History ({rejectedPrompts.length})
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="active">
            {activePrompts.length > 0 ? (
              activePrompts.map(renderPromptCard)
            ) : (
              <p>No active prompts found.</p>
            )}
          </TabsContent>
          
          <TabsContent value="candidates">
            {candidatePrompts.length > 0 ? (
              candidatePrompts.map(renderPromptCard)
            ) : (
              <p>No candidate prompts waiting for review.</p>
            )}
          </TabsContent>
          
          <TabsContent value="history">
            {rejectedPrompts.length > 0 ? (
              rejectedPrompts.map(renderPromptCard)
            ) : (
              <p>No rejected prompts in history.</p>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default PromptsPage;