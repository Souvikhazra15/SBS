const fs = require('fs')
const path = require('path')

function rm(dir) {
  try {
    const p = path.resolve(dir)
    if (fs.existsSync(p)) {
      fs.rmSync(p, { recursive: true, force: true })
      console.log('Removed', p)
    }
  } catch (e) {
    console.error('Failed to remove', dir, e)
  }
}

console.log('Cleaning project...')
rm('.next')
rm('.turbo')
rm('.cache')
rm('node_modules/.cache')
console.log('Done.')
