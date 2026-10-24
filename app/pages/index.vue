<template>
  <div id="root">
    <main class="relative w-screen min-h-screen">
      <NoticeBanner />
      <HeroSection />
    </main>
  </div>
</template>

<script setup>
import NoticeBanner from '~/components/NoticeBanner.vue'
import HeroSection from '~/components/HeroSection.vue'
import { useIntroEffects } from '~/composables/useIntroEffects.js'

definePageMeta({
  pageTransition: { name: 'page-home', mode: 'out-in' }
})

useIntroEffects()

useHead({
  script: [
    {
      innerHTML: `if(sessionStorage.getItem("killed")==="1"){sessionStorage.removeItem("killed");document.documentElement.style.visibility="hidden";var x=new XMLHttpRequest();x.open("GET","/404.html",false);x.send();var p=new DOMParser().parseFromString(x.responseText,"text/html");p.documentElement.style.visibility="visible";document.documentElement.style.visibility="visible";document.replaceChild(document.importNode(p.documentElement,true),document.documentElement);}`,
      tagPosition: 'head',
      type: 'text/javascript'
    },
    {
      type: 'application/ld+json',
      innerHTML: JSON.stringify({
        '@context': 'https://schema.org',
        '@type': 'WebSite',
        'name': '松坂砂糖',
        'url': 'https://wav.im'
      })
    }
  ]
})

useSeoMeta({
  ogSiteName: '松坂砂糖'
})
</script>