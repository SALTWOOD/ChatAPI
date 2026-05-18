import { useEffect } from 'react'

import homepageHtml from '../../homepage.html?raw'

export function HomepageScreen() {
  useEffect(() => {
    document.title = 'ChatAPI'
  }, [])

  return (
    <div className="homepage-shell">
      <iframe
        title="ChatAPI Homepage"
        srcDoc={homepageHtml}
        className="homepage-frame"
      />
    </div>
  )
}
