import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'
import { 
  THREE_ASTRO_CONFIG, 
  ZODIAC_COLORS, 
  HOUSE_COLORS,
  disposeResource, 
  createCanvasTexture,
  PLANET_ORBIT_RADII
} from './constants.js'

const ZODIAC_SYMBOLS = ['♈', '♉', '♊', '♋', '♌', '♍', '♎', '♏', '♐', '♑', '♒', '♓']
const HOUSE_NUMBERS = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']

export function useThreeScene() {
  let scene = null
  let camera = null
  let renderer = null
  let controls = null
  let container = null
  
  let animationId = null
  let isAnimating = false
  
  const texturesToDispose = []
  const geometriesToDispose = []
  const materialsToDispose = []
  
  const orbitRingsGroup = new THREE.Group()
  
  function init(containerElement, options = {}) {
    container = containerElement
    
    let width = containerElement.clientWidth || options.width || 600
    let height = containerElement.clientHeight || options.height || 600
    
    if (width <= 0 || height <= 0) {
      const rect = containerElement.getBoundingClientRect()
      width = rect.width || 600
      height = rect.height || 550
    }
    
    if (width <= 0 || height <= 0) {
      width = 600
      height = 550
    }
    
    scene = new THREE.Scene()
    scene.background = new THREE.Color(0x050510)
    scene.fog = new THREE.FogExp2(0x050510, 0.006)
    
    camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 300)
    camera.position.set(0, THREE_ASTRO_CONFIG.CAMERA_HEIGHT, THREE_ASTRO_CONFIG.CAMERA_DISTANCE)
    
    renderer = new THREE.WebGLRenderer({ 
      antialias: true,
      alpha: true,
      powerPreference: 'high-performance'
    })
    renderer.setSize(width, height)
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.shadowMap.enabled = true
    renderer.shadowMap.type = THREE.PCFSoftShadowMap
    renderer.toneMapping = THREE.ACESFilmicToneMapping
    renderer.toneMappingExposure = 1.3
    
    containerElement.appendChild(renderer.domElement)
    
    controls = new OrbitControls(camera, renderer.domElement)
    controls.enableDamping = true
    controls.dampingFactor = THREE_ASTRO_CONFIG.DAMPING_FACTOR
    controls.enableZoom = true
    controls.enablePan = false
    controls.minDistance = THREE_ASTRO_CONFIG.MIN_ZOOM
    controls.maxDistance = THREE_ASTRO_CONFIG.MAX_ZOOM
    controls.autoRotate = true
    controls.autoRotateSpeed = THREE_ASTRO_CONFIG.AUTO_ROTATE_SPEED
    controls.maxPolarAngle = Math.PI * 0.85
    controls.minPolarAngle = Math.PI * 0.15
    controls.target.set(0, 0, 0)
    
    addLights()
    createStarField()
    createOrbitRingsLayer()
    createZodiacRing()
    createHouseRing()
    
    scene.add(orbitRingsGroup)
    
    setTimeout(() => onResize(), 50)
    
    return {
      scene,
      camera,
      renderer,
      controls
    }
  }
  
  function addLights() {
    const ambientLight = new THREE.AmbientLight(0x404070, 0.5)
    scene.add(ambientLight)
    materialsToDispose.push(ambientLight)
    
    const hemiLight = new THREE.HemisphereLight(0x8899ff, 0x221133, 0.6)
    hemiLight.position.set(0, 20, 0)
    scene.add(hemiLight)
    materialsToDispose.push(hemiLight)
    
    const mainLight = new THREE.DirectionalLight(0xffeedd, 1.2)
    mainLight.position.set(15, 20, 10)
    mainLight.castShadow = true
    mainLight.shadow.mapSize.width = 2048
    mainLight.shadow.mapSize.height = 2048
    mainLight.shadow.camera.near = 0.5
    mainLight.shadow.camera.far = 100
    mainLight.shadow.camera.left = -30
    mainLight.shadow.camera.right = 30
    mainLight.shadow.camera.top = 30
    mainLight.shadow.camera.bottom = -30
    mainLight.shadow.bias = -0.0001
    scene.add(mainLight)
    materialsToDispose.push(mainLight)
    
    const fillLight = new THREE.DirectionalLight(0x6688ff, 0.4)
    fillLight.position.set(-12, 8, -10)
    scene.add(fillLight)
    materialsToDispose.push(fillLight)
    
    const rimLight = new THREE.PointLight(0xaa66ff, 0.8, 40)
    rimLight.position.set(0, -15, -15)
    scene.add(rimLight)
    materialsToDispose.push(rimLight)
    
    const topLight = new THREE.DirectionalLight(0xffffff, 0.3)
    topLight.position.set(0, 25, 0)
    scene.add(topLight)
    materialsToDispose.push(topLight)
    
    const bottomLight = new THREE.DirectionalLight(0x444488, 0.2)
    bottomLight.position.set(0, -15, 5)
    scene.add(bottomLight)
    materialsToDispose.push(bottomLight)
  }
  
  function createStarField() {
    const starGeometry = new THREE.BufferGeometry()
    const starCount = THREE_ASTRO_CONFIG.STAR_COUNT
    const positions = new Float32Array(starCount * 3)
    const colors = new Float32Array(starCount * 3)
    const sizes = new Float32Array(starCount)
    
    for (let i = 0; i < starCount; i++) {
      const i3 = i * 3
      const radius = THREE_ASTRO_CONFIG.STAR_RADIUS * (0.6 + Math.random() * 0.6)
      const theta = Math.random() * Math.PI * 2
      const phi = Math.acos(2 * Math.random() - 1)
      
      positions[i3] = radius * Math.sin(phi) * Math.cos(theta)
      positions[i3 + 1] = radius * Math.sin(phi) * Math.sin(theta)
      positions[i3 + 2] = radius * Math.cos(phi)
      
      const colorChoice = Math.random()
      if (colorChoice < 0.65) {
        colors[i3] = 1
        colors[i3 + 1] = 1
        colors[i3 + 2] = 1
      } else if (colorChoice < 0.8) {
        colors[i3] = 0.8
        colors[i3 + 1] = 0.85
        colors[i3 + 2] = 1
      } else if (colorChoice < 0.92) {
        colors[i3] = 1
        colors[i3 + 1] = 0.92
        colors[i3 + 2] = 0.8
      } else {
        colors[i3] = 1
        colors[i3 + 1] = 0.8
        colors[i3 + 2] = 0.85
      }
      
      sizes[i] = Math.random() * 0.2 + 0.08
    }
    
    starGeometry.setAttribute('position', new THREE.BufferAttribute(positions, 3))
    starGeometry.setAttribute('color', new THREE.BufferAttribute(colors, 3))
    starGeometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1))
    geometriesToDispose.push(starGeometry)
    
    const starMaterial = new THREE.PointsMaterial({
      size: 0.18,
      vertexColors: true,
      transparent: true,
      opacity: 0.98,
      sizeAttenuation: true,
      blending: THREE.AdditiveBlending,
      depthWrite: false
    })
    materialsToDispose.push(starMaterial)
    
    const stars = new THREE.Points(starGeometry, starMaterial)
    scene.add(stars)
  }
  
  function createOrbitRingsLayer() {
    const orbitRadii = []
    Object.values(PLANET_ORBIT_RADII).forEach(r => {
      if (!orbitRadii.includes(r)) {
        orbitRadii.push(r)
      }
    })
    orbitRadii.sort((a, b) => a - b)
    
    orbitRadii.forEach((radius, index) => {
      const orbitGeometry = new THREE.RingGeometry(
        radius - 0.015,
        radius + 0.015,
        64
      )
      geometriesToDispose.push(orbitGeometry)
      
      const alpha = 0.12 + (index * 0.02)
      const orbitMaterial = new THREE.MeshBasicMaterial({
        color: 0x403080,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: alpha
      })
      materialsToDispose.push(orbitMaterial)
      
      const orbitRing = new THREE.Mesh(orbitGeometry, orbitMaterial)
      orbitRing.rotation.x = Math.PI / 2
      orbitRingsGroup.add(orbitRing)
    })
  }
  
  function createZodiacRing() {
    const group = new THREE.Group()
    
    const ringGeometry = new THREE.RingGeometry(
      THREE_ASTRO_CONFIG.ZODIAC_RADIUS - 0.08,
      THREE_ASTRO_CONFIG.ZODIAC_RADIUS + 0.08,
      128
    )
    geometriesToDispose.push(ringGeometry)
    
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x6050a0,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.5
    })
    materialsToDispose.push(ringMaterial)
    
    const ring = new THREE.Mesh(ringGeometry, ringMaterial)
    ring.rotation.x = Math.PI / 2
    group.add(ring)
    
    for (let i = 0; i < 12; i++) {
      const angle = i * 30 * Math.PI / 180
      const innerRadius = THREE_ASTRO_CONFIG.ZODIAC_RADIUS - 0.4
      const outerRadius = THREE_ASTRO_CONFIG.ZODIAC_RADIUS + 0.4
      
      const lineGeometry = new THREE.BufferGeometry()
      const linePositions = new Float32Array(6)
      linePositions[0] = innerRadius * Math.cos(angle)
      linePositions[1] = 0.15
      linePositions[2] = innerRadius * Math.sin(angle)
      linePositions[3] = outerRadius * Math.cos(angle)
      linePositions[4] = 0.15
      linePositions[5] = outerRadius * Math.sin(angle)
      lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3))
      geometriesToDispose.push(lineGeometry)
      
      const lineMaterial = new THREE.LineBasicMaterial({
        color: ZODIAC_COLORS[i],
        transparent: true,
        opacity: 0.6
      })
      materialsToDispose.push(lineMaterial)
      
      const line = new THREE.Line(lineGeometry, lineMaterial)
      group.add(line)
      
      const sectorGeometry = new THREE.RingGeometry(
        innerRadius,
        outerRadius,
        32,
        1,
        angle - 15 * Math.PI / 180,
        30 * Math.PI / 180
      )
      geometriesToDispose.push(sectorGeometry)
      
      const sectorMaterial = new THREE.MeshBasicMaterial({
        color: ZODIAC_COLORS[i],
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.08
      })
      materialsToDispose.push(sectorMaterial)
      
      const sector = new THREE.Mesh(sectorGeometry, sectorMaterial)
      sector.rotation.x = Math.PI / 2
      group.add(sector)
      
      const midAngle = (i * 30 + 15) * Math.PI / 180
      const labelRadius = THREE_ASTRO_CONFIG.ZODIAC_RADIUS + 0.9
      const labelX = labelRadius * Math.cos(midAngle)
      const labelZ = labelRadius * Math.sin(midAngle)
      
      const { texture } = createCanvasTexture(128, 128, (ctx) => {
        ctx.clearRect(0, 0, 128, 128)
        ctx.font = 'bold 52px Arial'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        const colorHex = '#' + ZODIAC_COLORS[i].toString(16).padStart(6, '0')
        ctx.fillStyle = colorHex
        ctx.fillText(ZODIAC_SYMBOLS[i], 64, 64)
      })
      texturesToDispose.push(texture)
      
      const spriteMaterial = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity: 0.85
      })
      materialsToDispose.push(spriteMaterial)
      
      const sprite = new THREE.Sprite(spriteMaterial)
      sprite.position.set(labelX, 0.2, labelZ)
      sprite.scale.set(1.4, 1.4, 1)
      group.add(sprite)
    }
    
    group.rotation.x = THREE_ASTRO_CONFIG.ZODIAC_TILT
    group.userData = { type: 'zodiacRing' }
    scene.add(group)
  }
  
  function createHouseRing() {
    const group = new THREE.Group()
    
    const ringGeometry = new THREE.RingGeometry(
      THREE_ASTRO_CONFIG.HOUSE_RADIUS - 0.25,
      THREE_ASTRO_CONFIG.HOUSE_RADIUS + 0.25,
      128
    )
    geometriesToDispose.push(ringGeometry)
    
    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x8060c0,
      side: THREE.DoubleSide,
      transparent: true,
      opacity: 0.15
    })
    materialsToDispose.push(ringMaterial)
    
    const ring = new THREE.Mesh(ringGeometry, ringMaterial)
    ring.rotation.x = Math.PI / 2
    group.add(ring)
    
    for (let i = 0; i < 12; i++) {
      const sectorStartAngle = i * 30 * Math.PI / 180
      const sectorMidAngle = (i * 30 + 15) * Math.PI / 180
      
      const sectorGeometry = new THREE.RingGeometry(
        THREE_ASTRO_CONFIG.HOUSE_RADIUS - 0.25,
        THREE_ASTRO_CONFIG.HOUSE_RADIUS + 0.25,
        32,
        1,
        sectorStartAngle,
        30 * Math.PI / 180
      )
      geometriesToDispose.push(sectorGeometry)
      
      const sectorMaterial = new THREE.MeshBasicMaterial({
        color: HOUSE_COLORS[i],
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.06
      })
      materialsToDispose.push(sectorMaterial)
      
      const sector = new THREE.Mesh(sectorGeometry, sectorMaterial)
      sector.rotation.x = Math.PI / 2
      group.add(sector)
      
      const innerRadius = THREE_ASTRO_CONFIG.HOUSE_RADIUS - 0.3
      const outerRadius = THREE_ASTRO_CONFIG.HOUSE_RADIUS + 0.3
      
      const lineGeometry = new THREE.BufferGeometry()
      const linePositions = new Float32Array(6)
      linePositions[0] = innerRadius * Math.cos(sectorStartAngle)
      linePositions[1] = -0.1
      linePositions[2] = innerRadius * Math.sin(sectorStartAngle)
      linePositions[3] = outerRadius * Math.cos(sectorStartAngle)
      linePositions[4] = -0.1
      linePositions[5] = outerRadius * Math.sin(sectorStartAngle)
      lineGeometry.setAttribute('position', new THREE.BufferAttribute(linePositions, 3))
      geometriesToDispose.push(lineGeometry)
      
      const lineMaterial = new THREE.LineBasicMaterial({
        color: HOUSE_COLORS[i],
        transparent: true,
        opacity: 0.35
      })
      materialsToDispose.push(lineMaterial)
      
      const line = new THREE.Line(lineGeometry, lineMaterial)
      group.add(line)
      
      const labelRadius = THREE_ASTRO_CONFIG.HOUSE_RADIUS
      const labelX = labelRadius * Math.cos(sectorMidAngle)
      const labelZ = labelRadius * Math.sin(sectorMidAngle)
      
      const { texture } = createCanvasTexture(96, 96, (ctx) => {
        ctx.clearRect(0, 0, 96, 96)
        ctx.font = 'bold 36px Arial'
        ctx.textAlign = 'center'
        ctx.textBaseline = 'middle'
        const colorHex = '#' + HOUSE_COLORS[i].toString(16).padStart(6, '0')
        ctx.fillStyle = colorHex
        ctx.fillText(HOUSE_NUMBERS[i], 48, 48)
      })
      texturesToDispose.push(texture)
      
      const spriteMaterial = new THREE.SpriteMaterial({
        map: texture,
        transparent: true,
        opacity: 0.6
      })
      materialsToDispose.push(spriteMaterial)
      
      const sprite = new THREE.Sprite(spriteMaterial)
      sprite.position.set(labelX, -0.05, labelZ)
      sprite.scale.set(0.8, 0.8, 1)
      group.add(sprite)
    }
    
    group.rotation.x = THREE_ASTRO_CONFIG.ORBIT_TILT
    group.userData = { type: 'houseRing' }
    scene.add(group)
  }
  
  function startAnimation(onBeforeRender) {
    isAnimating = true
    
    function animate() {
      if (!isAnimating) return
      
      animationId = requestAnimationFrame(animate)
      
      const delta = 0.016
      
      if (controls) {
        controls.update()
      }
      
      if (onBeforeRender) {
        onBeforeRender(delta)
      }
      
      if (renderer && scene && camera) {
        renderer.render(scene, camera)
      }
    }
    
    animate()
  }
  
  function stopAnimation() {
    isAnimating = false
    if (animationId) {
      cancelAnimationFrame(animationId)
      animationId = null
    }
  }
  
  function onResize() {
    if (!container || !camera || !renderer) return
    
    let width = container.clientWidth
    let height = container.clientHeight
    
    if (width <= 0 || height <= 0) {
      const rect = container.getBoundingClientRect()
      width = rect.width || 600
      height = rect.height || 550
    }
    
    if (width <= 0 || height <= 0) {
      width = 600
      height = 550
    }
    
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }
  
  function registerForDispose(resource) {
    if (resource.geometry) {
      geometriesToDispose.push(resource.geometry)
    }
    if (resource.material) {
      if (Array.isArray(resource.material)) {
        resource.material.forEach(m => materialsToDispose.push(m))
      } else {
        materialsToDispose.push(resource.material)
      }
    }
    if (resource.texture) {
      texturesToDispose.push(resource.texture)
    }
  }
  
  function getScene() { return scene }
  function getCamera() { return camera }
  function getRenderer() { return renderer }
  function getControls() { return controls }
  
  function dispose() {
    stopAnimation()
    
    texturesToDispose.forEach(t => disposeResource(t))
    geometriesToDispose.forEach(g => disposeResource(g))
    materialsToDispose.forEach(m => disposeResource(m))
    
    if (controls) {
      controls.dispose()
    }
    
    if (renderer) {
      renderer.dispose()
      if (container && renderer.domElement) {
        container.removeChild(renderer.domElement)
      }
    }
    
    scene = null
    camera = null
    renderer = null
    controls = null
    container = null
    
    texturesToDispose.length = 0
    geometriesToDispose.length = 0
    materialsToDispose.length = 0
  }
  
  return {
    getScene,
    getCamera,
    getRenderer,
    getControls,
    init,
    startAnimation,
    stopAnimation,
    onResize,
    registerForDispose,
    dispose
  }
}
