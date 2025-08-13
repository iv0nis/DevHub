import { NextApiRequest, NextApiResponse } from 'next'

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'GET') {
    return handleGetSync(req, res)
  } else if (req.method === 'POST') {
    return handleTriggerSync(req, res)
  } else {
    return res.status(405).json({ error: 'Method not allowed' })
  }
}

async function handleGetSync(req: NextApiRequest, res: NextApiResponse) {
  try {
    // For MVP, return mock sync status
    const syncInfo = {
      is_synchronized: true,
      last_sync: new Date(Date.now() - 1000 * 60 * 5).toISOString(), // 5 minutes ago
      pending_syncs: [],
      sync_errors: [],
      documents: [
        {
          name: 'project_status.md',
          status: 'synced' as const,
          last_modified: new Date(Date.now() - 1000 * 60 * 15).toISOString()
        },
        {
          name: 'backlog_f1.yaml',
          status: 'synced' as const,
          last_modified: new Date(Date.now() - 1000 * 60 * 20).toISOString()
        },
        {
          name: 'blueprint.md',
          status: 'synced' as const,
          last_modified: new Date(Date.now() - 1000 * 60 * 60).toISOString()
        },
        {
          name: 'das_audit.log',
          status: 'synced' as const,
          last_modified: new Date(Date.now() - 1000 * 60 * 10).toISOString()
        }
      ]
    }

    res.status(200).json(syncInfo)
    
  } catch (error) {
    console.error('Error fetching sync status:', error)
    res.status(500).json({ 
      error: 'Failed to fetch sync status',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}

async function handleTriggerSync(req: NextApiRequest, res: NextApiResponse) {
  try {
    // For MVP, simulate sync trigger
    console.log('Manual sync triggered from web dashboard')
    
    // In production, this would trigger the actual sync process
    // await triggerDocumentSync()
    
    res.status(200).json({ 
      success: true, 
      message: 'Sync triggered successfully' 
    })
    
  } catch (error) {
    console.error('Error triggering sync:', error)
    res.status(500).json({ 
      error: 'Failed to trigger sync',
      message: error instanceof Error ? error.message : 'Unknown error'
    })
  }
}