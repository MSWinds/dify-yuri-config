'use client'
import type { Locale } from '@/i18n-config'
import dynamic from 'next/dynamic'
import Image from 'next/image'
import Divider from '@/app/components/base/divider'
import LocaleSigninSelect from '@/app/components/base/select/locale-signin'
import { useGlobalPublicStore } from '@/context/global-public-context'
import { useLocale } from '@/context/i18n'
import { setLocaleOnClient } from '@/i18n-config'
import { languages } from '@/i18n-config/language'

// Avoid rendering the logo and theme selector on the server
const DifyLogo = dynamic(() => import('@/app/components/base/logo/dify-logo'), {
  ssr: false,
  loading: () => <div className="h-7 w-16 bg-transparent" />,
})
const ThemeSelector = dynamic(() => import('@/app/components/base/theme-selector'), {
  ssr: false,
  loading: () => <div className="size-8 bg-transparent" />,
})

const COVER_SRC = '/images/CGU%20Cover1.png'

const Header = () => {
  const locale = useLocale()
  const systemFeatures = useGlobalPublicStore(s => s.systemFeatures)

  return (
    <div className="relative w-full overflow-hidden rounded-t-2xl">
      {/* Always-fill mode: use object-cover so there's no reserved background area (may crop if aspect ratio differs). */}
      <div className="absolute inset-0">
        <Image
          src={COVER_SRC}
          alt=""
          fill
          priority
          // `sizes` must reflect real render width; otherwise Next will serve a small image and it will look blurry on 2K/4K.
          sizes="100vw"
          quality={95}
          className="object-cover object-center"
        />
        {/* Light overlay to unify contrast across different banners */}
        <div className="absolute inset-0 bg-black/10" />
      </div>

      <div className="relative flex h-[88px] w-full items-center justify-between px-6 md:h-[180px]">
        {/* Backplates make the controls readable in both light/dark themes on top of the cover image */}
        <div className="rounded-xl border border-effects-highlight bg-background-default-subtle px-3 py-2 shadow-[0_1px_14px_rgba(0,0,0,0.18)]">
          {systemFeatures.branding.enabled && systemFeatures.branding.login_page_logo
            ? (
                <img
                  src={systemFeatures.branding.login_page_logo}
                  className="block h-7 w-auto object-contain"
                  alt="logo"
                />
              )
            : <DifyLogo size="large" />}
        </div>

        <div className="rounded-xl border border-effects-highlight bg-background-default-subtle px-2 py-2 shadow-[0_1px_14px_rgba(0,0,0,0.18)]">
          <div className="flex items-center gap-1">
            <LocaleSigninSelect
              value={locale}
              items={languages.filter(item => item.supported)}
              onChange={(value) => {
                setLocaleOnClient(value as Locale)
              }}
            />
            <Divider type="vertical" className="mx-0 ml-2 h-4" />
            <ThemeSelector />
          </div>
        </div>
      </div>
    </div>
  )
}

export default Header
