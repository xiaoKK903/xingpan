import * as THREE from 'three'
import { PLANET_SYMBOLS } from './constants.js'

const HOVER_THROTTLE_MS = 50

export function useInteractionManager(
  getContainer,
  getCamera,
  getRenderer,
  getAllPlanetMeshes,
  highlightPlanet,
  resetPlanetHighlight,
  resetAllPlanets,
  onPlanetSelect,
  onPointerLeave
) {
  const raycaster = new THREE.Raycaster()
  const pointer = new THREE.Vector2()
  
  let lastHoverTime = 0
  let currentHoveredPlanet = null
  let isHovering = false
  
  let eventListeners = []
  
  function setupEventListeners(domElement) {
    removeEventListeners()
    
    const onPointerMove = createThrottledPointerMove()
    const onClick = handleClick
    const onPointerLeaveHandler = handlePointerLeave
    
    domElement.addEventListener('pointermove', onPointerMove)
    domElement.addEventListener('click', onClick)
    domElement.addEventListener('pointerleave', onPointerLeaveHandler)
    
    eventListeners = [
      { element: domElement, type: 'pointermove', handler: onPointerMove },
      { element: domElement, type: 'click', handler: onClick },
      { element: domElement, type: 'pointerleave', handler: onPointerLeaveHandler }
    ]
  }
  
  function removeEventListeners() {
    eventListeners.forEach(({ element, type, handler }) => {
      element.removeEventListener(type, handler)
    })
    eventListeners.length = 0
  }
  
  function createThrottledPointerMove() {
    return function(event) {
      const now = Date.now()
      const shouldCheck = now - lastHoverTime >= HOVER_THROTTLE_MS
      
      updatePointerPosition(event)
      
      if (shouldCheck) {
        lastHoverTime = now
        checkHover()
      }
    }
  }
  
  function updatePointerPosition(event) {
    const container = getContainer()
    const renderer = getRenderer()
    
    if (!container || !renderer) return
    
    const rect = container.getBoundingClientRect()
    
    pointer.x = (event.clientX - rect.left) / rect.width * 2 - 1
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1
  }
  
  function checkHover() {
    const camera = getCamera()
    const renderer = getRenderer()
    
    if (!camera || !raycaster) return null
    
    raycaster.setFromCamera(pointer, camera)
    
    const planetMeshes = getAllPlanetMeshes()
    
    if (planetMeshes.length === 0) return null
    
    const intersects = raycaster.intersectObjects(planetMeshes)
    
    if (intersects.length > 0) {
      const hoveredMesh = intersects[0].object
      const planetName = hoveredMesh.userData.planetName
      
      if (planetName !== currentHoveredPlanet) {
        if (currentHoveredPlanet) {
          const currentMesh = planetMeshes.find(m => m.userData.planetName === currentHoveredPlanet)
          if (currentMesh && !currentMesh.userData.isSelected) {
            resetPlanetHighlight(currentHoveredPlanet)
          }
        }
        
        if (!hoveredMesh.userData.isSelected) {
          highlightPlanet(planetName, false)
        }
        
        currentHoveredPlanet = planetName
        
        if (renderer && renderer.domElement) {
          renderer.domElement.style.cursor = 'pointer'
        }
      }
      
      isHovering = true
    } else {
      if (currentHoveredPlanet) {
        const currentMesh = planetMeshes.find(m => m.userData.planetName === currentHoveredPlanet)
        if (currentMesh && !currentMesh.userData.isSelected) {
          resetPlanetHighlight(currentHoveredPlanet)
        }
        currentHoveredPlanet = null
      }
      
      if (renderer && renderer.domElement) {
        renderer.domElement.style.cursor = 'grab'
      }
      
      isHovering = false
    }
    
    return {
      isHovering,
      hoveredPlanet: currentHoveredPlanet,
      hoveredSymbol: currentHoveredPlanet ? PLANET_SYMBOLS[currentHoveredPlanet] || '★' : null
    }
  }
  
  function handleClick(event) {
    updatePointerPosition(event)
    
    const camera = getCamera()
    
    if (!camera || !raycaster) return
    
    raycaster.setFromCamera(pointer, camera)
    
    const planetMeshes = getAllPlanetMeshes()
    const intersects = raycaster.intersectObjects(planetMeshes)
    
    if (intersects.length > 0) {
      const clickedMesh = intersects[0].object
      const planetName = clickedMesh.userData.planetName
      
      resetAllPlanets()
      
      highlightPlanet(planetName, true)
      
      currentHoveredPlanet = planetName
      
      if (onPlanetSelect) {
        onPlanetSelect(clickedMesh.userData.planetData, planetName)
      }
    } else {
      if (onPlanetSelect) {
        onPlanetSelect(null, null)
      }
    }
  }
  
  function handlePointerLeave() {
    const planetMeshes = getAllPlanetMeshes()
    const renderer = getRenderer()
    
    if (currentHoveredPlanet) {
      const currentMesh = planetMeshes.find(m => m.userData.planetName === currentHoveredPlanet)
      if (currentMesh && !currentMesh.userData.isSelected) {
        resetPlanetHighlight(currentHoveredPlanet)
      }
      currentHoveredPlanet = null
    }
    
    isHovering = false
    
    if (renderer && renderer.domElement) {
      renderer.domElement.style.cursor = 'grab'
    }
    
    if (onPointerLeave) {
      onPointerLeave()
    }
  }
  
  function forceHoverCheck() {
    return checkHover()
  }
  
  function getCurrentHoveredPlanet() {
    return currentHoveredPlanet
  }
  
  function getCurrentHoveredSymbol() {
    return currentHoveredPlanet ? PLANET_SYMBOLS[currentHoveredPlanet] || '★' : null
  }
  
  function dispose() {
    removeEventListeners()
    currentHoveredPlanet = null
    isHovering = false
  }
  
  return {
    setupEventListeners,
    removeEventListeners,
    forceHoverCheck,
    getCurrentHoveredPlanet,
    getCurrentHoveredSymbol,
    dispose
  }
}
