import Paper from '@mui/material/Paper'
import Typography from '@mui/material/Typography'
import Button from '@mui/material/Button'
import Box from '@mui/material/Box'
import ContentCopy from '@mui/icons-material/ContentCopy'
import RestartAlt from '@mui/icons-material/RestartAlt'

type Props = {
  story: string
  onRestart: () => void
}

export default function StoryResult({ story, onRestart }: Props) {
  const handleCopy = () => {
    navigator.clipboard.writeText(story)
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        生成的故事
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
        叙事风格：第一人称回忆录成文
      </Typography>
      <Box
        sx={{
          p: 2,
          bgcolor: 'grey.50',
          borderRadius: 2,
          whiteSpace: 'pre-wrap',
          maxHeight: 480,
          overflow: 'auto',
        }}
      >
        <Typography component="div" variant="body1">
          {story}
        </Typography>
      </Box>
      <Box sx={{ display: 'flex', gap: 2, mt: 2, flexWrap: 'wrap' }}>
        <Button
          variant="outlined"
          startIcon={<ContentCopy />}
          onClick={handleCopy}
        >
          复制全文
        </Button>
        <Button
          variant="contained"
          startIcon={<RestartAlt />}
          onClick={onRestart}
        >
          重新开始
        </Button>
      </Box>
    </Paper>
  )
}
